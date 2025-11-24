import pyomo.environ as pyo
from a_inputs import strom_verfügbarkeiten_23, df_parameter, traeger_dict

# Vorbereitung Verfügbarkeits-Dictionaries (kann auch in inputs.py, hier zur besseren Kapselung)
verf_s_dict = {}
df_param_index = set(df_parameter.index)
strom_verf_dict = strom_verfügbarkeiten_23.to_dict('index')
# determine valid electricity technologies from the availability dataframe that also exist in the parameter index
gueltige_s_techs = [t for t in strom_verfügbarkeiten_23.columns if t in df_parameter.index]
for t in gueltige_s_techs:
    for ti in strom_verfügbarkeiten_23.index:
        verf_s_dict[(t, ti)] = strom_verf_dict[ti][t]
        verf_s_dict[(t, ti)] = strom_verfügbarkeiten_23.loc[ti, t]

# verf_wae_dict = {}
# gueltige_wae_techs = [t for t in df_erzeuger_waerme.columns if t in df_parameter.index]
# for t in gueltige_wae_techs:
#     for ti in df_erzeuger_waerme.index:
#         verf_wae_dict[(t, ti)] = df_erzeuger_waerme.loc[ti, t]

# def define_constraints(model, df_bedarf):
#     model.Strombedarf = pyo.Param(model.T, initialize=df_bedarf['Strom_Gesamt_Bedarf [MW]'].to_dict())
#     # model.Waermebedarf = pyo.Param(model.T, initialize=df_bedarf['Wärme'].to_dict())

#     model.Verf_s = pyo.Param(model.techs, model.T, initialize=verf_s_dict, default=0)
#     # model.Verf_wae = pyo.Param(model.techs, model.T, initialize=verf_wae_dict, default=0)

#     def strom_bedarfsdeckung_regel(m, time):
#         stromerzeuger_summe = sum(
#             m.inst_leistung[t, 'Strom'] * m.Verf_s[t, time]
#             for t in m.techs if m.art_map[t] == 'Erzeuger' and m.traeger_map[t] == 'Strom'
#         )
#         stromspeicher_summe = sum(
#             m.stromspeicher_leistung[t, time]
#             for t in m.techs if m.art_map[t] == 'Speicher' and m.traeger_map[t] == 'Strom'
#         )
        
#         return stromerzeuger_summe + stromspeicher_summe >= m.Strombedarf[time]

#     model.strom_bedarfsdeckung_bedingung = pyo.Constraint(model.T, rule=strom_bedarfsdeckung_regel)

    # def waerme_erzeuger_regel(m, time):
    #     waermeerzeuger_summe = sum(
    #         m.inst_leistung[t, 'Wärme'] * m.Verf_wae[t, time]
    #         for t in m.techs if m.art_map[t] == 'Erzeuger' and m.traeger_map[t] == 'Wärme'
    #     )
    #     return waermeerzeuger_summe >= m.Waermebedarf[time]

    # model.waerme_erzeuger_bedingung = pyo.Constraint(model.T, rule=waerme_erzeuger_regel)

 

    # return model

def define_constraints(model, df_bedarf):
    model.Strombedarf = pyo.Param(model.T, initialize=df_bedarf['Strom_Gesamt_Bedarf [MW]'].to_dict())
    model.Verf_s = pyo.Param(model.techs, model.T, initialize=verf_s_dict, default=0)

    def strom_bedarfsdeckung_regel(m, time):
        # Erzeugung
        erzeugung = sum(
            m.inst_leistung[t, c] * m.Verf_s[t, time]
            for t, c in m.inst_leistung_index
            if m.art_map[t] == 'Erzeuger'
        )
        
        # Batteriespeicher (15min-Auflösung, immer verfügbar)
        batterie_beitrag = 0
        if hasattr(m, 'batterie_leistung'):
            batterie_techs = [t for t in m.techs 
                            if m.art_map[t] == 'Speicher' 
                            and 'Batterie' in t]
            batterie_beitrag = sum(m.batterie_leistung[s, time] for s in batterie_techs)
        
        # Pumpspeicher (stündlich → auf 15min interpolieren)
        pump_beitrag = 0
        if hasattr(m, 'pump_leistung'):
            pump_techs = [t for t in m.techs 
                         if m.art_map[t] == 'Speicher' 
                         and 'Pump' in t]
            
            if pump_techs:
                # Finde nächste volle Stunde (abrunden)
                time_list = list(m.T)
                time_idx = time_list.index(time)
                hourly_idx = time_idx // 4  # Ganzzahldivision: 0,1,2,3 → 0; 4,5,6,7 → 1
                hourly_time = list(m.T_hourly)[hourly_idx]
                
                # Pumpspeicher-Leistung der aktuellen Stunde nutzen
                pump_beitrag = sum(m.pump_leistung[s, hourly_time] for s in pump_techs)

                # Wasserstoffspeicher (stündlich → auf 15min interpolieren)
                h2_beitrag = 0
                if hasattr(m, 'h2_leistung'):
                    h2_techs = [t for t in m.techs 
                                if m.art_map[t] == 'Speicher' 
                                and 'Wasserstoff' in t]
                    
                    if h2_techs:
                        # Finde nächste volle Stunde (abrunden)
                        hourly_idx = time_idx // 4
                        hourly_time = list(m.T_hourly)[hourly_idx]
                        
                        # Wasserstoffspeicher-Leistung der aktuellen Stunde nutzen
                        h2_beitrag = sum(m.h2_leistung[s, hourly_time] for s in h2_techs)

                return erzeugung + batterie_beitrag + pump_beitrag + h2_beitrag >= m.Strombedarf[time]
        
        return erzeugung + batterie_beitrag + pump_beitrag >= m.Strombedarf[time]

    model.strom_bedarfsdeckung_bedingung = pyo.Constraint(model.T, rule=strom_bedarfsdeckung_regel)
    return model


print('Ende c_constraints.py')