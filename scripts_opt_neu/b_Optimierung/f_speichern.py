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
        sheets_written = 0
        
        for var_name, data in results.items():
            # Nur inst_leistung und kapazitaet (keine Zeitreihen)
            if var_name in ['inst_leistung', 'kapazitaet', 'batterie_kapazitaet', 'pump_kapazitaet', 'h2_kapazitaet']:
                # ✅ WICHTIG: Prüfe, ob data leer ist
                if not data:
                    print(f"⚠ Variable '{var_name}' ist leer (übersprungen)")
                    continue
                
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
                sheets_written += 1
        
        # ✅ Falls KEINE Sheets geschrieben wurden, erstelle Dummy-Sheet
        if sheets_written == 0:
            df_dummy = pd.DataFrame({'Info': ['Keine installierten Leistungen gefunden']})
            df_dummy.to_excel(writer, sheet_name='Info', index=False)
            print("⚠ WARNUNG: Keine installierten Leistungen gefunden!")
    
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
            
            if not soc_data:
                continue
            
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
            
            if not soc_data:
                continue
            
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
    
    # Wasserstoffspeicher (stündliche Auflösung)
    if hasattr(model, 'h2_stand'):
        h2_techs = [s for s in model.techs 
                   if model.art_map[s] == 'Speicher' 
                   and 'Wasserstoff' in s]
        
        for tech in h2_techs:
            # SOC
            soc_data = {t: pyo.value(model.h2_stand[tech, t]) 
                       for t in model.T_hourly 
                       if model.h2_stand[tech, t].value is not None}
            
            if not soc_data:
                continue
            
            # Leistung
            power_data = {t: pyo.value(model.h2_leistung[tech, t]) 
                         for t in model.T_hourly 
                         if model.h2_leistung[tech, t].value is not None}
            
            # Kapazität
            capacity = pyo.value(model.h2_kapazitaet[tech])
            
            # DataFrame erstellen
            df_h2 = pd.DataFrame({
                'Zeitstempel': list(soc_data.keys()),
                'SOC [MWh]': list(soc_data.values()),
                'Leistung [MW]': list(power_data.values()),
                'Kapazität [MWh]': [capacity] * len(soc_data),
                'SOC [%]': [soc_data[t] / capacity * 100 if capacity > 0 else 0 
                           for t in soc_data.keys()]
            })
            df_h2.set_index('Zeitstempel', inplace=True)
            
            speicher_daten[f'{tech}_H2'] = df_h2
    
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
            # Zeitschritt-Dauer ermitteln (15min für Batterie, 1h für Pump/H2)
            if '_Batterie' in speicher_name:
                timestep_hours = 0.25  # 15min
            else:
                timestep_hours = 1.0  # 1h
            
            stats = {
                'Speicher': speicher_name,
                'Zeitschritte': len(df_speicher),
                'Kapazität [MWh]': df_speicher['Kapazität [MWh]'].iloc[0],
                'Max SOC [MWh]': df_speicher['SOC [MWh]'].max(),
                'Min SOC [MWh]': df_speicher['SOC [MWh]'].min(),
                'Durchschn. SOC [MWh]': df_speicher['SOC [MWh]'].mean(),
                'Max Entladung [MW]': df_speicher['Leistung [MW]'].max(),
                'Max Ladung [MW]': df_speicher['Leistung [MW]'].min(),
                'Gesamte Entladung [MWh]': df_speicher[df_speicher['Leistung [MW]'] > 0]['Leistung [MW]'].sum() * timestep_hours,
                'Gesamte Ladung [MWh]': abs(df_speicher[df_speicher['Leistung [MW]'] < 0]['Leistung [MW]'].sum()) * timestep_hours,
            }
            statistiken.append(stats)
        
        df_stats = pd.DataFrame(statistiken)
        
        with pd.ExcelWriter(r'data\b_Optimierung\opt_speicher_statistiken.xlsx') as writer:
            df_stats.to_excel(writer, sheet_name='Speicher_Statistiken', index=False)
            print(f"\nSpeicher-Statistiken gespeichert: {len(df_stats)} Speicher")
    
    print("\n=== SPEICHERN ABGESCHLOSSEN ===")
    print(f"1. Installierte Leistungen: data\\b_Optimierung\\opt_inst_Leistung.xlsx")
    if speicher_daten:
        print(f"2. Speicher-Zeitreihen: data\\b_Optimierung\\opt_speicher_zeitreihen.xlsx")
        print(f"3. Speicher-Statistiken: data\\b_Optimierung\\opt_speicher_statistiken.xlsx")
    
    # ========== KOSTEN-BERECHNUNG ==========
    WACC = 0.05  # 5% Standard für Energieprojekte
    
    from a_inputs import kosten, df_parameter, lebensdauer
    per_tech = {}

    def calculate_crf(lifetime, wacc=WACC):
        """Berechnet Capital Recovery Factor"""
        try:
            lifetime = float(lifetime)
        except Exception:
            return 1.0
        if lifetime <= 0:
            return 1.0
        if wacc == 0:
            return 1.0 / lifetime
        return (wacc * (1 + wacc) ** lifetime) / ((1 + wacc) ** lifetime - 1)

    # Numerische Berechnung der annualisierten CAPEX pro Technologie
    for (t, c) in getattr(model, 'inst_leistung_index', []):
        try:
            installed_val = pyo.value(model.inst_leistung[t, c])
        except Exception:
            continue

        if installed_val is None:
            continue

        # untere Grenze aus df_parameter (falls vorhanden)
        if t in df_parameter.index:
            try:
                lower_bound = float(df_parameter.loc[t, 'untere Grenze [MW]'])
            except Exception:
                lower_bound = 0.0
        else:
            lower_bound = 0.0

        added_capacity = max(0.0, installed_val - lower_bound)

        unit_cost = float(kosten.get(t, 0.0))
        capex_total = unit_cost * added_capacity

        life = lebensdauer.get(t, 1)
        crf = calculate_crf(life, WACC)
        annualized_capex = capex_total * crf

        per_tech.setdefault(t, 0.0)
        per_tech[t] += float(annualized_capex)

    print("\n=== ANNUALISIERTE KOSTEN ===")
    for t, val in sorted(per_tech.items(), key=lambda x: x[1], reverse=True):
        print(f"  {t:30s}: {val:>15,.2f} EUR/Jahr")

    total_annualized = sum(per_tech.values())
    print(f"\n{'Gesamt annualisierte CAPEX':30s}: {total_annualized:>15,.2f} EUR/Jahr")
    
    # Speichere Kosten in opt_inst_Leistung.xlsx
    if per_tech:
        with pd.ExcelWriter(r'data\b_Optimierung\opt_inst_Leistung.xlsx', mode='a', if_sheet_exists='replace') as writer:
            df_costs = pd.DataFrame({
                'Technologie': list(per_tech.keys()),
                'Annualisierte CAPEX [EUR/Jahr]': list(per_tech.values())
            })
            df_costs = df_costs.sort_values('Annualisierte CAPEX [EUR/Jahr]', ascending=False)
            df_costs.set_index('Technologie', inplace=True)
            df_costs.to_excel(writer, sheet_name='Kosten')
            
            # Gesamtkosten als separate Zeile
            df_total = pd.DataFrame({
                'Annualisierte CAPEX [EUR/Jahr]': [total_annualized]
            }, index=['GESAMT'])
            df_total.to_excel(writer, sheet_name='Kosten', startrow=len(df_costs)+2)
    
    return results

print("Ende der f_speichern.py Datei")