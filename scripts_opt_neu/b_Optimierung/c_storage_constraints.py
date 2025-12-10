# import pyomo.environ as pyo
# from a_inputs import strom_verfügbarkeiten_23, df_parameter, traeger_dict

import pyomo.environ as pyo
import a_inputs

def stromspeicher_regeln(model):
    """
    Differenzierte Speichermodellierung:
    - Batteriespeicher: 15min-Auflösung, schnelle Reaktion
    - Pumpspeicher: stündliche Auflösung, trägere nachgelagerte Reaktion
    """
    time_list = list(model.T)
    time_hourly = list(model.T_hourly)
    # Speicher identifizieren
    alle_speicher = [t for t in model.techs 
                     if model.art_map[t] == 'Speicher' 
                     and model.traeger_map[t] == 'Strom']
    
    if not alle_speicher:
        print("Keine Stromspeicher gefunden")
        return model
    
    # Klassifizierung: Batterie vs. Pumpspeicher
    batterie_techs = [s for s in alle_speicher if 'Batterie' in s]
    pump_techs = [s for s in alle_speicher if 'Pump' in s]
    
    print(f"Batteriespeicher (15min): {batterie_techs}")
    print(f"Pumpspeicher (1h): {pump_techs}")
    
       
    # ========== BATTERIESPEICHER (15min-Auflösung) ==========
    if batterie_techs:
        # Kapazität (einmal pro Speicher)
        model.batterie_kapazitaet = pyo.Var(
            batterie_techs,
            domain=pyo.NonNegativeReals,
            bounds=lambda m, s: (
                a_inputs.df_parameter.loc[s, 'untere Kapagrenze [MWh]'],
                a_inputs.df_parameter.loc[s, 'obere Kapagrenze [MWh]']
            )
        )
        
        # SOC und Leistung für ALLE 15min-Schritte
        model.batterie_stand = pyo.Var(
            batterie_techs, 
            model.T,
            domain=pyo.NonNegativeReals
        )
        
        model.batterie_leistung = pyo.Var(
            batterie_techs,
            model.T,
            domain=pyo.Reals
        )

        # Leistungsgrenzen als Constraints statt als Bounds (um variable/Expressions zu erlauben)
        def batterie_power_upper_rule(m, s, t):
            return m.batterie_leistung[s, t] <= m.inst_leistung[s, 'Strom']
        model.batterie_power_upper = pyo.Constraint(
            batterie_techs, model.T, rule=batterie_power_upper_rule
        )

        def batterie_power_lower_rule(m, s, t):
            return m.batterie_leistung[s, t] >= -m.inst_leistung[s, 'Strom']
        model.batterie_power_lower = pyo.Constraint(
            batterie_techs, model.T, rule=batterie_power_lower_rule
        )
        
        # Kapazitätsgrenze
        def batterie_level_constraint_rule(m, s, t):
            return m.batterie_stand[s, t] <=m.batterie_kapazitaet[s]
        
        model.batterie_level_constraint = pyo.Constraint(
            batterie_techs,
            model.T,
            rule=batterie_level_constraint_rule
        )
        
        def batterie_capa_crate_constraint_rule(m, s, t):
            return m.batterie_kapazitaet[s] <= m.inst_leistung[s, 'Strom']/a_inputs.c_rate[s]
        
        model.batterie_capa_crate_constraint = pyo.Constraint(
            batterie_techs,
            model.T,
            rule=batterie_capa_crate_constraint_rule
        )
        
        # Anfangsbedingung
        def batterie_init_rule(m, s):
            first_time = time_list[0]
            return m.batterie_stand[s, first_time] == 0.5*m.batterie_kapazitaet[s]
        
        model.batterie_init = pyo.Constraint(batterie_techs, rule=batterie_init_rule)
        
        # Bilanzgleichung (15min-Schritte, 0.25h)
        def batterie_balance_rule(m, s, t):
            time_idx = time_list.index(t)
            if time_idx == 0:
                return pyo.Constraint.Skip
            
            prev_time = time_list[time_idx - 1]
            eta = a_inputs.df_parameter.loc[s, 'Wirkungsgrad']
            
            return m.batterie_stand[s, t] == (
                m.batterie_stand[s, prev_time] - 
                m.batterie_leistung[s, t] * eta * 0.25  # 0.25h = 15min
            )
        
        model.batterie_balance = pyo.Constraint(
            batterie_techs,
            model.T,
            rule=batterie_balance_rule
        )
        
        print(f"  Batterie: {len(batterie_techs)} × {len(time_list)} = {len(batterie_techs) * len(time_list)} Variablen")
    
      # Zyklische Bedingung für konsistente Jahressimulation
        def batterie_cyclic_rule(m, s):
            first_time = time_list[0]
            last_time = time_list[-1]
            return m.batterie_stand[s, last_time] == m.batterie_stand[s, first_time]
        
        model.batterie_cyclic = pyo.Constraint(
            batterie_techs,
            rule=batterie_cyclic_rule
        )
        
        print(f"  Batterie: Zyklische Bedingung aktiviert (Anfangs-SOC = End-SOC)")
       # ========== PUMPSPEICHER (stündlich, OHNE Binärvariablen) ==========
    if pump_techs:
        model.pump_kapazitaet = pyo.Var(
            pump_techs,
            domain=pyo.NonNegativeReals,
            bounds=lambda m, s: (
                a_inputs.df_parameter.loc[s, 'untere Kapagrenze [MWh]'],
                a_inputs.df_parameter.loc[s, 'obere Kapagrenze [MWh]']
            )
        )
        
        model.pump_stand = pyo.Var(
            pump_techs, 
            model.T_hourly,
            domain=pyo.NonNegativeReals
        )
        
        model.pump_leistung = pyo.Var(
            pump_techs,
            model.T_hourly,
            domain=pyo.Reals
        )

        def pump_power_upper_rule(m, s, t):
            return m.pump_leistung[s, t] <= m.inst_leistung[s, 'Strom']
        model.pump_power_upper = pyo.Constraint(
            pump_techs, model.T_hourly, rule=pump_power_upper_rule
        )

        def pump_power_lower_rule(m, s, t):
            return m.pump_leistung[s, t] >= -m.inst_leistung[s, 'Strom']
        model.pump_power_lower = pyo.Constraint(
            pump_techs, model.T_hourly, rule=pump_power_lower_rule
        )
        
        def pump_level_constraint_rule(m, s, t):
            return m.pump_stand[s, t] <= m.pump_kapazitaet[s]
        model.pump_level_constraint = pyo.Constraint(
            pump_techs, model.T_hourly, rule=pump_level_constraint_rule
        )
        
        def pump_capa_crate_constraint_rule(m, s, t):
            return m.pump_kapazitaet[s] <= m.inst_leistung[s, 'Strom']/a_inputs.c_rate[s]
        model.pump_capa_crate_constraint = pyo.Constraint(
            pump_techs,
            model.T_hourly,
            rule=pump_capa_crate_constraint_rule
        )
        
        def pump_init_rule(m, s):
            first_time = time_hourly[0]
            return m.pump_stand[s, first_time] == 0.5*m.pump_kapazitaet[s]
        model.pump_init = pyo.Constraint(pump_techs, rule=pump_init_rule)
        
        def pump_balance_rule(m, s, t):
            time_idx = time_hourly.index(t)
            if time_idx == 0:
                return pyo.Constraint.Skip
            
            prev_time = time_hourly[time_idx - 1]
            eta = a_inputs.df_parameter.loc[s, 'Wirkungsgrad']
            
            return m.pump_stand[s, t] == (
                m.pump_stand[s, prev_time] - 
                m.pump_leistung[s, t] * eta * 1.0
            )
        model.pump_balance = pyo.Constraint(
            pump_techs, model.T_hourly, rule=pump_balance_rule
        )
        
        # VEREINFACHTE TRÄGHEIT: Leistungsänderung begrenzen (statt Binärvariablen)
        def pump_ramping_upper_rule(m, s, t):
            """Maximale Erhöhung der Leistung pro Stunde"""
            time_idx = time_hourly.index(t)
            if time_idx == 0:
                return pyo.Constraint.Skip
            
            prev_time = time_hourly[time_idx - 1]
            max_ramp = m.inst_leistung[s, 'Strom'] * 0.8  # Max 80% Änderung pro Stunde
            
            return m.pump_leistung[s, t] - m.pump_leistung[s, prev_time] <= max_ramp
        
        def pump_ramping_lower_rule(m, s, t):
            """Maximale Reduktion der Leistung pro Stunde"""
            time_idx = time_hourly.index(t)
            if time_idx == 0:
                return pyo.Constraint.Skip
            
            prev_time = time_hourly[time_idx - 1]
            max_ramp = m.inst_leistung[s, 'Strom'] * 0.8
            
            return m.pump_leistung[s, t] - m.pump_leistung[s, prev_time] >= -max_ramp
        
        model.pump_ramping_upper = pyo.Constraint(
            pump_techs, model.T_hourly, rule=pump_ramping_upper_rule
        )
        model.pump_ramping_lower = pyo.Constraint(
            pump_techs, model.T_hourly, rule=pump_ramping_lower_rule
        )
        
        print(f"  Pumpspeicher: {len(pump_techs)} × {len(time_hourly)} Variablen (mit Ramping-Limit)")

        # Zyklische Bedingung für konsistente Jahressimulation
        def pump_cyclic_rule(m, s):
            first_time = time_hourly[0]
            last_time = time_hourly[-1]
            return m.pump_stand[s, last_time] == m.pump_stand[s, first_time]

        model.pump_cyclic = pyo.Constraint(
            pump_techs,
            rule=pump_cyclic_rule
        )

        print(f"  Pumpspeicher: Zyklische Bedingung aktiviert (Anfangs-SOC = End-SOC)")

        return model
       # ========== WASSERSTOFFSPEICHER (stündlich, noch trägere als Pumpspeicher) ==========
def wasserstoffspeicher_regeln(model):
        # Speicher identifizieren
    alle_speicher = [t for t in model.techs 
                     if model.art_map[t] == 'Speicher' 
                     and model.traeger_map[t] == 'Wasserstoff']
    
    if not alle_speicher:
        print("Keine Wasserstoffspeicher gefunden")
        return model
   
    time_hourly = list(model.T_hourly)
    
    
    h2_speicher_techs = [s for s in alle_speicher if 'Wasserstoff' in s or 'H2' in s]
    
    print(f"Wasserstoffspeicher (1h): {h2_speicher_techs}")
    
    
              
    if h2_speicher_techs:
                print(f"Wasserstoffspeicher (1h, sehr träge): {h2_speicher_techs}")
                
                model.h2_kapazitaet = pyo.Var(
                    h2_speicher_techs,
                    domain=pyo.NonNegativeReals,
                    bounds=lambda m, s: (
                        a_inputs.df_parameter.loc[s, 'untere Kapagrenze [MWh]'],
                        a_inputs.df_parameter.loc[s, 'obere Kapagrenze [MWh]']
                    )
                )
                
                model.h2_stand = pyo.Var(
                    h2_speicher_techs, 
                    model.T_hourly,
                    domain=pyo.NonNegativeReals
                )
                
                model.h2_leistung = pyo.Var(
                    h2_speicher_techs,
                    model.T_hourly,
                    domain=pyo.Reals
                )

                def h2_power_upper_rule(m, s, t):
                    return m.h2_leistung[s, t] <= m.inst_leistung[s, 'Wasserstoff']
                model.h2_power_upper = pyo.Constraint(
                    h2_speicher_techs, model.T_hourly, rule=h2_power_upper_rule
                )

                def h2_power_lower_rule(m, s, t):
                    return m.h2_leistung[s, t] >= -m.inst_leistung[s, 'Wasserstoff']
                model.h2_power_lower = pyo.Constraint(
                    h2_speicher_techs, model.T_hourly, rule=h2_power_lower_rule
                )
                
                def h2_level_constraint_rule(m, s, t):
                    return m.h2_stand[s, t] <= m.h2_kapazitaet[s]
                model.h2_level_constraint = pyo.Constraint(
                    h2_speicher_techs, model.T_hourly, rule=h2_level_constraint_rule
                )
                
                def h2_capa_crate_constraint_rule(m, s, t):
                    return m.h2_kapazitaet[s] <= m.inst_leistung[s, 'Wasserstoff']/a_inputs.c_rate[s]
                model.h2_capa_crate_constraint = pyo.Constraint(
                    h2_speicher_techs, model.T_hourly, rule=h2_capa_crate_constraint_rule
                )
                
                def h2_init_rule(m, s):
                    first_time = time_hourly[0]
                    return m.h2_stand[s, first_time] == 0.5*m.h2_kapazitaet[s]
                model.h2_init = pyo.Constraint(h2_speicher_techs, rule=h2_init_rule)
                
                def h2_balance_rule(m, s, t):
                    time_idx = time_hourly.index(t)
                    if time_idx == 0:
                        return pyo.Constraint.Skip
                    
                    prev_time = time_hourly[time_idx - 1]
                    eta = a_inputs.df_parameter.loc[s, 'Wirkungsgrad']
                    
                    return m.h2_stand[s, t] == (
                        m.h2_stand[s, prev_time] - 
                        m.h2_leistung[s, t] * eta * 1.0
                    )
                model.h2_balance = pyo.Constraint(
                    h2_speicher_techs, model.T_hourly, rule=h2_balance_rule
                )
                
                # SEHR TRÄGE: Noch stärkere Leistungsbegrenzung als bei Pumpspeichern
                def h2_ramping_upper_rule(m, s, t):
                    """Maximale Erhöhung der Leistung pro Stunde """
                    time_idx = time_hourly.index(t)
                    if time_idx == 0:
                        return pyo.Constraint.Skip
                    
                    prev_time = time_hourly[time_idx - 1]
                    max_ramp = m.inst_leistung[s, 'Wasserstoff'] * 0.5  # Max 50% Änderung pro Stunde
                    
                    return m.h2_leistung[s, t] - m.h2_leistung[s, prev_time] <= max_ramp
                
                def h2_ramping_lower_rule(m, s, t):
                    """Maximale Reduktion der Leistung pro Stunde """
                    time_idx = time_hourly.index(t)
                    if time_idx == 0:
                        return pyo.Constraint.Skip
                    
                    prev_time = time_hourly[time_idx - 1]
                    max_ramp = m.inst_leistung[s, 'Wasserstoff'] * 0.5
                    
                    return m.h2_leistung[s, t] - m.h2_leistung[s, prev_time] >= -max_ramp
                
                model.h2_ramping_upper = pyo.Constraint(
                    h2_speicher_techs, model.T_hourly, rule=h2_ramping_upper_rule
                )
                model.h2_ramping_lower = pyo.Constraint(
                    h2_speicher_techs, model.T_hourly, rule=h2_ramping_lower_rule
                )
                
                print(f"  Wasserstoffspeicher: {len(h2_speicher_techs)} × {len(time_hourly)} Variablen (mit starkem Ramping-Limit)")

                # Zyklische Bedingung für konsistente Jahressimulation
                def h2_cyclic_rule(m, s):
                    first_time = time_hourly[0]
                    last_time = time_hourly[-1]
                    return m.h2_stand[s, last_time] == m.h2_stand[s, first_time]

                model.h2_cyclic = pyo.Constraint(
                    h2_speicher_techs,
                    rule=h2_cyclic_rule
                )

                print(f"  Wasserstoffspeicher: Zyklische Bedingung aktiviert (Anfangs-SOC = End-SOC)")
    
    print(f"\nWasserstoffspeichermodell erstellt (OHNE Binärvariablen)")
    print(f"  Gesamt Variablen: ~{len(h2_speicher_techs) * len(time_hourly) * 3} (Kapazität, Stand, Leistung)")
    
    return model

print('Ende c_storage_constraints.py')


