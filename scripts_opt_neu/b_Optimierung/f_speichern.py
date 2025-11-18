import pandas as pd
import pyomo.environ as pyo

# Funktion zum Speichern der Ergebnisse
def speichere_ergebnisse(model):
    results = {}
    
    # Alle Variablen sammeln
    for v in model.component_objects(pyo.Var, active=True):
        var_name = v.getname()
        results[var_name] = {}
        for index in v:
            if v[index].value is not None:
                results[var_name][index] = pyo.value(v[index])
    
    # ========== INSTALLIERTE LEISTUNGEN (wie bisher) ==========
    with pd.ExcelWriter(r'data\b_Optimierung\opt_inst_Leistung.xlsx') as writer:
        for var_name, data in results.items():
            # Nur inst_leistung und kapazitaet (keine Zeitreihen)
            if var_name in ['inst_leistung', 'kapazitaet', 'batterie_kapazitaet', 'pump_kapazitaet']:
                df = pd.DataFrame.from_dict(data, orient='index', columns=['Wert'])
                
                # Index-Struktur je nach Variable
                if isinstance(list(data.keys())[0], tuple):
                    if len(list(data.keys())[0]) == 2:  # (Technologie, Träger)
                        df['Technologie'] = df.index.str[0]
                        df['Träger'] = df.index.str[1]
                        df = df[['Technologie', 'Träger', 'Wert']]
                        df = df.set_index('Technologie')
                    else:  # Nur Technologie
                        df['Technologie'] = df.index
                        df = df[['Technologie', 'Wert']]
                        df = df.set_index('Technologie')
                
                df.to_excel(writer, sheet_name=var_name[:31])
    
    # ========== SPEICHER-ZEITREIHEN ==========
    speicher_daten = {}
    
    # Batteriespeicher (15min-Auflösung)
    if hasattr(model, 'batterie_stand'):
        batterie_techs = [s for s in model.techs 
                         if model.art_map[s] == 'Speicher' 
                         and 'Batterie' in s]
        
        for tech in batterie_techs:
            # SOC (State of Charge)
            soc_data = {t: pyo.value(model.batterie_stand[tech, t]) 
                       for t in model.T 
                       if model.batterie_stand[tech, t].value is not None}
            
            # Leistung (positiv = Entladen, negativ = Laden)
            power_data = {t: pyo.value(model.batterie_leistung[tech, t]) 
                         for t in model.T 
                         if model.batterie_leistung[tech, t].value is not None}
            
            # Kapazität
            capacity = pyo.value(model.batterie_kapazitaet[tech])
            
            # DataFrame erstellen
            df_batterie = pd.DataFrame({
                'Zeitstempel': list(soc_data.keys()),
                'SOC [MWh]': list(soc_data.values()),
                'Leistung [MW]': list(power_data.values()),
                'Kapazität [MWh]': [capacity] * len(soc_data),
                'SOC [%]': [soc_data[t] / capacity * 100 if capacity > 0 else 0 
                           for t in soc_data.keys()]
            })
            df_batterie.set_index('Zeitstempel', inplace=True)
            
            speicher_daten[f'{tech}_Batterie'] = df_batterie
    
    # Pumpspeicher (stündliche Auflösung)
    if hasattr(model, 'pump_stand'):
        pump_techs = [s for s in model.techs 
                     if model.art_map[s] == 'Speicher' 
                     and 'Pump' in s]
        
        for tech in pump_techs:
            # SOC
            soc_data = {t: pyo.value(model.pump_stand[tech, t]) 
                       for t in model.T_hourly 
                       if model.pump_stand[tech, t].value is not None}
            
            # Leistung
            power_data = {t: pyo.value(model.pump_leistung[tech, t]) 
                         for t in model.T_hourly 
                         if model.pump_leistung[tech, t].value is not None}
            
            # Aktivierungsstatus
            aktiv_data = {}
            if hasattr(model, 'pump_aktiv'):
                aktiv_data = {t: pyo.value(model.pump_aktiv[tech, t]) 
                             for t in model.T_hourly 
                             if model.pump_aktiv[tech, t].value is not None}
            
            # Kapazität
            capacity = pyo.value(model.pump_kapazitaet[tech])
            
            # DataFrame erstellen
            df_pump = pd.DataFrame({
                'Zeitstempel': list(soc_data.keys()),
                'SOC [MWh]': list(soc_data.values()),
                'Leistung [MW]': list(power_data.values()),
                'Kapazität [MWh]': [capacity] * len(soc_data),
                'SOC [%]': [soc_data[t] / capacity * 100 if capacity > 0 else 0 
                           for t in soc_data.keys()],
            })
            
            if aktiv_data:
                df_pump['Aktiv'] = [aktiv_data[t] for t in soc_data.keys()]
            
            df_pump.set_index('Zeitstempel', inplace=True)
            
            speicher_daten[f'{tech}_Pump'] = df_pump
    
    # Speicher-Zeitreihen in Excel schreiben
    if speicher_daten:
        with pd.ExcelWriter(r'data\b_Optimierung\opt_speicher_zeitreihen.xlsx') as writer:
            for speicher_name, df_speicher in speicher_daten.items():
                df_speicher.to_excel(writer, sheet_name=speicher_name[:31])
                print(f"Speicher-Zeitreihe gespeichert: {speicher_name} ({len(df_speicher)} Zeitschritte)")
    
    # ========== ZUSAMMENFASSUNG: Speicherstatistiken ==========
    if speicher_daten:
        statistiken = []
        
        for speicher_name, df_speicher in speicher_daten.items():
            stats = {
                'Speicher': speicher_name,
                'Zeitschritte': len(df_speicher),
                'Kapazität [MWh]': df_speicher['Kapazität [MWh]'].iloc[0],
                'Max SOC [MWh]': df_speicher['SOC [MWh]'].max(),
                'Min SOC [MWh]': df_speicher['SOC [MWh]'].min(),
                'Durchschn. SOC [MWh]': df_speicher['SOC [MWh]'].mean(),
                'Max Entladung [MW]': df_speicher['Leistung [MW]'].max(),
                'Max Ladung [MW]': df_speicher['Leistung [MW]'].min(),
                'Gesamte Entladung [MWh]': df_speicher[df_speicher['Leistung [MW]'] > 0]['Leistung [MW]'].sum() * 0.25,  # 15min
                'Gesamte Ladung [MWh]': abs(df_speicher[df_speicher['Leistung [MW]'] < 0]['Leistung [MW]'].sum()) * 0.25,
            }
            statistiken.append(stats)
        
        df_stats = pd.DataFrame(statistiken)
        
        with pd.ExcelWriter(r'data\b_Optimierung\opt_speicher_statistiken.xlsx') as writer:
            df_stats.to_excel(writer, sheet_name='Speicher_Statistiken', index=False)
            print(f"\nSpeicher-Statistiken gespeichert: {len(df_stats)} Speicher")
    
    print("\n=== SPEICHERN ABGESCHLOSSEN ===")
    print(f"1. Installierte Leistungen: data\\b_Optimierung\\opt_inst_Leistung.xlsx")
    print(f"2. Speicher-Zeitreihen: data\\b_Optimierung\\opt_speicher_zeitreihen.xlsx")
    print(f"3. Speicher-Statistiken: data\\b_Optimierung\\opt_speicher_statistiken.xlsx")
    
    return results

print("Ende der f_speichern.py Datei")