import pyomo.environ as pyo
from a_inputs import (strom_verfügbarkeiten_23, df_parameter, traeger_dict, 
                      solarthermie_verfügbarkeiten_23, wirkungsgrade, art_dict)

# Vorbereitung Verfügbarkeits-Dictionaries
verf_s_dict = {}
df_param_index = set(df_parameter.index)
strom_verf_dict = strom_verfügbarkeiten_23.to_dict('index')
gueltige_s_techs = [t for t in strom_verfügbarkeiten_23.columns if t in df_parameter.index]
for t in gueltige_s_techs:
    for ti in strom_verfügbarkeiten_23.index:
        verf_s_dict[(t, ti)] = strom_verfügbarkeiten_23.loc[ti, t]

verf_wae_dict = {}
gueltige_wae_techs = [t for t in solarthermie_verfügbarkeiten_23.columns if t in df_parameter.index]
for t in gueltige_wae_techs:
    for ti in solarthermie_verfügbarkeiten_23.index:
        verf_wae_dict[(t, ti)] = solarthermie_verfügbarkeiten_23.loc[ti, t]

DEBUG_DISABLE_HEAT = False
DEBUG_DISABLE_STORAGE = False

def define_constraints(model, df_bedarf, df_bedarf_daily):
    model.Strombedarf = pyo.Param(model.T, initialize=df_bedarf['Strom_Gesamt_Bedarf [MW]'].to_dict())
    model.Verf_s = pyo.Param(model.techs, model.T, initialize=verf_s_dict, default=0)

    if not DEBUG_DISABLE_HEAT:
        model.Wärmebedarf = pyo.Param(model.T_daily, initialize=df_bedarf_daily['Wärme_Gesamt_Bedarf [MWh]'].to_dict())
        model.Verf_wae = pyo.Param(model.techs, model.T_daily, initialize=verf_wae_dict, default=0)
    
    # ========== STROM-BEDARFSDECKUNG ==========
    def strom_bedarfsdeckung_regel(m, time):
        strom_erzeuger = [
            (t, c) for t, c in m.inst_leistung_index
            if m.art_map[t] == 'Erzeuger' and m.traeger_map[t] == 'Strom'
        ]
        
        if not strom_erzeuger:
            return pyo.Constraint.Feasible
        
        erzeugung = sum(
            m.inst_leistung[t, c] * m.Verf_s[t, time]
            for t, c in strom_erzeuger
        )
        
        time_list = list(m.T)
        time_idx = time_list.index(time)
        hourly_idx = time_idx // 4
        hourly_time = list(m.T_hourly)[hourly_idx]
        
        # Speicher-Beiträge
        batterie_beitrag = 0
        if not DEBUG_DISABLE_STORAGE and hasattr(m, 'batterie_leistung'):
            batterie_techs = [t for t in m.techs 
                            if m.art_map[t] == 'Speicher' 
                            and 'Batterie' in t]
            if batterie_techs:
                batterie_beitrag = sum(m.batterie_leistung[s, time] for s in batterie_techs)
        
        pump_beitrag = 0
        if not DEBUG_DISABLE_STORAGE and hasattr(m, 'pump_leistung'):
            pump_techs = [t for t in m.techs 
                         if m.art_map[t] == 'Speicher' 
                         and 'Pump' in t]
            if pump_techs:
                pump_beitrag = sum(m.pump_leistung[s, hourly_time] for s in pump_techs)
        
        h2_beitrag = 0
        if not DEBUG_DISABLE_STORAGE and hasattr(m, 'h2_leistung'):
            h2_techs = [t for t in m.techs 
                        if m.art_map[t] == 'Speicher' 
                        and 'Wasserstoff' in t]
            if h2_techs:
                h2_beitrag = sum(m.h2_leistung[s, hourly_time] for s in h2_techs)

        # ✅ KORRIGIERT: Wandler-Beiträge
        wandler_output_strom = 0
        wandler_input_strom = 0
        
        if hasattr(m, 'wandler_output'):
            # Output: Wandler, die Strom ERZEUGEN (Brennstoffzelle, Verbrennungsmotor)
            strom_output_wandler = [
                t for t in m.techs
                if m.art_map[t] == 'Wandler' 
                and m.traeger_map[t] == 'Strom'
            ]
            
            if strom_output_wandler:
                wandler_output_strom = sum(
                    m.wandler_output[t, time]
                    for t in strom_output_wandler
                )
            
            # Input: Wandler, die Strom VERBRAUCHEN (Wärmepumpe, Elektrolyseur, Stromheizung)
            strom_input_wandler = [
                t for t in m.techs
                if m.art_map[t] == 'Wandler'
                and t in df_parameter.index
                and df_parameter.loc[t, 'Input'] == 'Strom'
            ]
            
            if strom_input_wandler:
                # ✅ Input = Output / Wirkungsgrad
                wandler_input_strom = sum(
                    m.wandler_output[t, time] / wirkungsgrade[t] if wirkungsgrade[t] > 0 else 0
                    for t in strom_input_wandler
                )
        
        return (erzeugung + batterie_beitrag + pump_beitrag + h2_beitrag + wandler_output_strom 
                >= m.Strombedarf[time] + wandler_input_strom)

    model.strom_bedarfsdeckung_bedingung = pyo.Constraint(model.T, rule=strom_bedarfsdeckung_regel)

    # ========== WÄRME-BEDARFSDECKUNG ==========
    if not DEBUG_DISABLE_HEAT:
        def wärme_bedarfsdeckung_regel(m, time):
            waerme_erzeuger = [
                (t, c) for t, c in m.inst_leistung_index
                if m.art_map[t] == 'Erzeuger' and m.traeger_map[t] == 'Wärme'
            ]
            
            if not waerme_erzeuger and not hasattr(m, 'wandler_output'):
                return pyo.Constraint.Feasible
            
            erzeugung_täglich = 0
            if waerme_erzeuger:
                erzeugung_täglich = sum(
                    m.inst_leistung[t, c] * 24 * (m.Verf_wae[t, time] if (t, time) in m.Verf_wae else 1)
                    for t, c in waerme_erzeuger
                )

            wandler_output_waerme = 0
            
            if hasattr(m, 'wandler_output'):
                time_list_daily = list(m.T_daily)
                day_idx = time_list_daily.index(time)
                
                time_list_15min = list(m.T)
                start_idx = day_idx * 96
                end_idx = (day_idx + 1) * 96
                times_of_day = time_list_15min[start_idx:end_idx]
                
                # ✅ Wärme-Wandler (Wärmepumpen, Wasserstoffheizung, Stromheizung)
                waerme_output_wandler = [
                    t for t in m.techs
                    if m.art_map[t] == 'Wandler'
                    and m.traeger_map[t] == 'Wärme'
                ]
                
                if waerme_output_wandler:
                    wandler_output_waerme = sum(
                        sum(
                            m.wandler_output[t, time_15min] * 0.25  # MW → MWh (15min)
                            for time_15min in times_of_day
                        )
                        for t in waerme_output_wandler
                    )

            return erzeugung_täglich + wandler_output_waerme >= m.Wärmebedarf[time]
        
        model.wärme_bedarfsdeckung_bedingung = pyo.Constraint(model.T_daily, rule=wärme_bedarfsdeckung_regel)
        
        waerme_techs = [t for t, c in model.inst_leistung_index 
                        if model.art_map[t] == 'Erzeuger' and model.traeger_map[t] == 'Wärme']
        wandler_waerme = [t for t in model.techs if model.art_map[t] == 'Wandler' 
                         and model.traeger_map[t] == 'Wärme']
        print(f"✓ Wärme-Constraint aktiviert:")
        print(f"  - {len(waerme_techs)} Erzeuger: {waerme_techs}")
        if wandler_waerme:
            print(f"  - {len(wandler_waerme)} Wandler: {wandler_waerme}")
    
    if DEBUG_DISABLE_STORAGE:
        print("⚠ DEBUG: Speicher-Beitrag DEAKTIVIERT!")
    else:
        print("✓ Speicher-Beitrag AKTIVIERT")

    # ========== WASSERSTOFF-BILANZ (VOLLSTÄNDIG NEU!) ==========
    # ✅ Diese Bilanz fehlt komplett! Daher wird H2 produziert, aber nie genutzt.
    
    # Identifiziere H2-Wandler
    h2_produktion_wandler = [
        t for t in model.techs
        if model.art_map[t] == 'Wandler'
        and t in df_parameter.index
        and df_parameter.loc[t, 'Energieträger'] == 'Wasserstoff'  # Output ist H2
    ]
    
    h2_verbrauch_wandler = [
        t for t in model.techs
        if model.art_map[t] == 'Wandler'
        and t in df_parameter.index
        and df_parameter.loc[t, 'Input'] == 'Wasserstoff'  # Input ist H2
    ]
    
    if h2_produktion_wandler or h2_verbrauch_wandler:
        print(f"✓ Wasserstoff-Wandler gefunden:")
        print(f"  - Produktion: {h2_produktion_wandler}")
        print(f"  - Verbrauch: {h2_verbrauch_wandler}")
        
        # ✅ NEUE CONSTRAINT: H2-Bilanz zu jedem Zeitpunkt
        def h2_bilanz_zeitlich_regel(m, time):
            # Zeitindex 15min → stündlich
            time_list = list(m.T)
            time_idx = time_list.index(time)
            hourly_idx = time_idx // 4
            hourly_time = list(m.T_hourly)[hourly_idx]
            
            # H2-Produktion (z.B. Elektrolyseur)
            h2_produktion = 0
            if h2_produktion_wandler and hasattr(m, 'wandler_output'):
                h2_produktion = sum(
                    m.wandler_output[t, time]
                    for t in h2_produktion_wandler
                )
            
            # H2-Verbrauch (z.B. Brennstoffzelle, Wasserstoffheizung)
            h2_verbrauch = 0
            if h2_verbrauch_wandler and hasattr(m, 'wandler_output'):
                h2_verbrauch = sum(
                    m.wandler_output[t, time] / wirkungsgrade[t] if wirkungsgrade[t] > 0 else 0
                    for t in h2_verbrauch_wandler
                )
            
            # H2-Speicher-Änderung (wenn vorhanden)
            h2_speicher_änderung = 0
            if hasattr(m, 'h2_leistung'):
                h2_techs = [s for s in m.techs if m.art_map[s] == 'Speicher' and 'Wasserstoff' in s]
                if h2_techs:
                    # h2_leistung > 0: Speicher wird GELEERT (liefert H2)
                    # h2_leistung < 0: Speicher wird GEFÜLLT (nimmt H2 auf)
                    h2_speicher_änderung = sum(m.h2_leistung[s, hourly_time] for s in h2_techs)
            
            # ✅ Bilanz: Produktion + Speicher-Entnahme >= Verbrauch + Speicher-Befüllung
            # Umformuliert: Produktion >= Verbrauch - Speicher-Änderung
            # (Speicher-Änderung wird automatisch in c_storage_constraints.py geregelt)
            
            # Vereinfachte Form: Produktion muss mindestens Verbrauch decken
            # (Speicher-Logik erfolgt in h2_balance_rule)
            return h2_produktion >= h2_verbrauch
        
        model.h2_bilanz_zeitlich = pyo.Constraint(model.T, rule=h2_bilanz_zeitlich_regel)
        print("  ✓ H2-Bilanz-Constraint (zeitlich) aktiviert")

    # ========== SOLARFLÄCHEN-KONKURRENZ ==========
    def solar_flächen_konkurrenz_regel(m):
        solarthermie_techs = [
            (t, c) for t, c in m.inst_leistung_index
            if 'Solarthermie' in t and m.traeger_map[t] == 'Wärme'
        ]
        photovoltaik_techs = [
            (t, c) for t, c in m.inst_leistung_index
            if 'Fotovoltaik' in t and m.traeger_map[t] == 'Strom'
        ]
        
        if not solarthermie_techs and not photovoltaik_techs:
            return pyo.Constraint.Feasible
        
        solarthermie_leistung = sum(m.inst_leistung[t, c] for t, c in solarthermie_techs) if solarthermie_techs else 0
        photovoltaik_leistung = sum(m.inst_leistung[t, c] for t, c in photovoltaik_techs) if photovoltaik_techs else 0
        
        max_flächenleistung = 1000000
        return solarthermie_leistung * 0.5 + photovoltaik_leistung <= max_flächenleistung
    
    model.solar_flächen_konkurrenz_bedingung = pyo.Constraint(rule=solar_flächen_konkurrenz_regel)
    print(f"✓ Solarflächen-Konkurrenz-Constraint aktiviert (Max: {1000000} MW)")
    
    return model

print('Ende c_constraints.py')