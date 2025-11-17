import pyomo.environ as pyo
from a_inputs import strom_verfügbarkeiten_23, df_parameter, traeger_dict

# Vorbereitung Verfügbarkeits-Dictionaries (kann auch in inputs.py, hier zur besseren Kapselung)
verf_s_dict = {}
gueltige_s_techs = [t for t in strom_verfügbarkeiten_23.columns if t in df_parameter.index and traeger_dict[t] == 'Strom']
for t in gueltige_s_techs:
    for ti in strom_verfügbarkeiten_23.index:
        verf_s_dict[(t, ti)] = strom_verfügbarkeiten_23.loc[ti, t]

# verf_wae_dict = {}
# gueltige_wae_techs = [t for t in df_erzeuger_waerme.columns if t in df_parameter.index]
# for t in gueltige_wae_techs:
#     for ti in df_erzeuger_waerme.index:
#         verf_wae_dict[(t, ti)] = df_erzeuger_waerme.loc[ti, t]

def define_constraints(model, df_bedarf):
    model.Strombedarf = pyo.Param(model.T, initialize=df_bedarf['Strom_Gesamt_Bedarf [MW]'].to_dict())
    # model.Waermebedarf = pyo.Param(model.T, initialize=df_bedarf['Wärme'].to_dict())

    model.Verf_s = pyo.Param(model.techs, model.T, initialize=verf_s_dict, default=0)
    # model.Verf_wae = pyo.Param(model.techs, model.T, initialize=verf_wae_dict, default=0)

    def strom_bedarfsdeckung_regel(m, time):
        stromerzeuger_summe = sum(
            m.inst_leistung[t, 'Strom'] * m.Verf_s[t, time]
            for t in m.techs if m.art_map[t] == 'Erzeuger' and m.traeger_map[t] == 'Strom'
        )
        # stromspeicher_summe = sum(
        #     m.stromspeicher_leistung[t, time]
        #     for t in m.techs if m.art_map[t] == 'Speicher' and m.traeger_map[t] == 'Strom'
        # )
        # hier muss wieder speicher hinzugefügt werden
        return stromerzeuger_summe  >= m.Strombedarf[time]

    model.strom_bedarfsdeckung_bedingung = pyo.Constraint(model.T, rule=strom_bedarfsdeckung_regel)

    # def waerme_erzeuger_regel(m, time):
    #     waermeerzeuger_summe = sum(
    #         m.inst_leistung[t, 'Wärme'] * m.Verf_wae[t, time]
    #         for t in m.techs if m.art_map[t] == 'Erzeuger' and m.traeger_map[t] == 'Wärme'
    #     )
    #     return waermeerzeuger_summe >= m.Waermebedarf[time]

    # model.waerme_erzeuger_bedingung = pyo.Constraint(model.T, rule=waerme_erzeuger_regel)

    # Weitere Funktionen wie stromspeicher_regeln() und weitere_speicher_regeln() können analog hier definiert und importiert werden

    return model

def stromspeicher_regeln(model):
    # Hier kommen alle Regeln für Stromspeicher wie im Originalcode, importierbar oder definiert
    # ...
    return model

def weitere_speicher_regeln(model):
    # Weitere Speicherbedingungen analog original
    # ...
    return model