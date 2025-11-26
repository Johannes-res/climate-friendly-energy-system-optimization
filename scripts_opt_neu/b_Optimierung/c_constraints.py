import pyomo.environ as pyo
from a_inputs import strom_verfügbarkeiten_23, df_parameter, traeger_dict, solarthermie_verfügbarkeiten_23

# Vorbereitung Verfügbarkeits-Dictionaries (kann auch in inputs.py, hier zur besseren Kapselung)
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


DEBUG_DISABLE_HEAT = False  # Temporär zum Testen
DEBUG_DISABLE_STORAGE = False  # Temporär zum Testen - deaktiviert Speicher-Beitrag

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

def define_constraints(model, df_bedarf, df_bedarf_daily):
    model.Strombedarf = pyo.Param(model.T, initialize=df_bedarf['Strom_Gesamt_Bedarf [MW]'].to_dict())
    model.Verf_s = pyo.Param(model.techs, model.T, initialize=verf_s_dict, default=0)

    if not DEBUG_DISABLE_HEAT:
        model.Wärmebedarf = pyo.Param(model.T_daily, initialize=df_bedarf_daily['Wärme_Gesamt_Bedarf [MWh]'].to_dict())
        model.Verf_wae = pyo.Param(model.techs, model.T_daily, initialize=verf_wae_dict, default=0)

    def strom_bedarfsdeckung_regel(m, time):
        # Erzeugung (immer aktiv)
        erzeugung = sum(
            m.inst_leistung[t, c] * m.Verf_s[t, time]
            for t, c in m.inst_leistung_index
            if m.art_map[t] == 'Erzeuger' and m.traeger_map[t] == 'Strom'
        )

        # Batteriespeicher (nur wenn DEBUG_DISABLE_STORAGE = False)
        batterie_beitrag = 0
        if not DEBUG_DISABLE_STORAGE and hasattr(m, 'batterie_leistung'):
            batterie_techs = [t for t in m.techs
                            if m.art_map[t] == 'Speicher'
                            and 'Batterie' in t]
            batterie_beitrag = sum(m.batterie_leistung[s, time] for s in batterie_techs)

        # Pumpspeicher (nur wenn DEBUG_DISABLE_STORAGE = False)
        pump_beitrag = 0
        if not DEBUG_DISABLE_STORAGE and hasattr(m, 'pump_leistung'):
            pump_techs = [t for t in m.techs
                         if m.art_map[t] == 'Speicher'
                         and 'Pump' in t]

            if pump_techs:
                time_list = list(m.T)
                time_idx = time_list.index(time)
                hourly_idx = time_idx // 4

                if hourly_idx < len(list(m.T_hourly)):
                    hourly_time = list(m.T_hourly)[hourly_idx]
                    pump_beitrag = sum(m.pump_leistung[s, hourly_time] for s in pump_techs)

        # Wasserstoffspeicher (nur wenn DEBUG_DISABLE_STORAGE = False)
        h2_beitrag = 0
        if not DEBUG_DISABLE_STORAGE and hasattr(m, 'h2_leistung'):
            h2_techs = [t for t in m.techs
                       if m.art_map[t] == 'Speicher'
                       and ('Wasserstoff' in t or 'H2' in t)]

            if h2_techs:
                time_list = list(m.T)
                time_idx = time_list.index(time)
                hourly_idx = time_idx // 4

                if hourly_idx < len(list(m.T_hourly)):
                    hourly_time = list(m.T_hourly)[hourly_idx]
                    h2_beitrag = sum(m.h2_leistung[s, hourly_time] for s in h2_techs)

        return erzeugung + batterie_beitrag + pump_beitrag + h2_beitrag >= m.Strombedarf[time]

    model.strom_bedarfsdeckung_bedingung = pyo.Constraint(model.T, rule=strom_bedarfsdeckung_regel)

    if not DEBUG_DISABLE_HEAT:
        def wärme_bedarfsdeckung_regel(m, time):
            erzeugung_täglich = sum(
                m.inst_leistung[t, c] * 24 * (m.Verf_wae[t, time] if (t, time) in m.Verf_wae else 1)
                for t, c in m.inst_leistung_index
                if m.art_map[t] == 'Erzeuger' and m.traeger_map[t] == 'Wärme'
            )
            return erzeugung_täglich >= m.Wärmebedarf[time]

        model.wärme_bedarfsdeckung_bedingung = pyo.Constraint(model.T_daily, rule=wärme_bedarfsdeckung_regel)
        print("✓ Wärme-Constraint aktiviert")
    else:
        print("⚠ DEBUG: Wärme-Constraint DEAKTIVIERT!")

    # Debug-Status ausgeben
    if DEBUG_DISABLE_STORAGE:
        print("⚠ DEBUG: Speicher-Beitrag zur Bedarfsdeckung DEAKTIVIERT!")
        print("  → Nur Erzeuger-Leistung wird berücksichtigt")
    else:
        print("✓ Speicher-Beitrag zur Bedarfsdeckung AKTIVIERT")

    return model


print('Ende c_constraints.py')