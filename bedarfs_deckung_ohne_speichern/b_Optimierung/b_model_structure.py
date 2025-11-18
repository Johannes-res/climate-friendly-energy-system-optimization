import pyomo.environ as pyo
from a_inputs import technologien, energietraeger, technologieart, traeger_dict, art_dict, kosten
#Erstellen des pyomo Modells
def create_energy_system_model(df_bedarf):
    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=df_bedarf.index, ordered=True)
    return model

#Definieren der Variablen mittels pyomo-Sets und -Params
# aus inputs.py werden die Hilfslisten und -dicts genutzt um die indizierten Variablen zu definieren und deren Grenzen zu setzen
def define_variables(model, df_parameter):
    model.techs = pyo.Set(initialize=technologien, ordered=True)
    model.traeger = pyo.Set(initialize=energietraeger, ordered=True)
    model.art = pyo.Set(initialize=technologieart, ordered=True)
    
    model.traeger_map = pyo.Param(model.techs, initialize=traeger_dict, within=pyo.Any)
    model.art_map = pyo.Param(model.techs, initialize=art_dict, within=pyo.Any)
    
    model.inst_leistung_index = [(t, c) for t in model.techs for c in model.traeger if traeger_dict[t] == c]
    model.inst_leistung = pyo.Var(
        model.inst_leistung_index,
        domain=pyo.NonNegativeReals,
        bounds=lambda m, t, c: (
            df_parameter.loc[t, 'untere Grenze [MW]'],
            df_parameter.loc[t, 'obere Grenze [MW]']
        )
    )
    # model.kapazitaet_index = [(t, c) for t in model.techs for c in model.traeger if art_dict[t] == 'Speicher' and traeger_dict[t] == c]
    # model.kapazitaet = pyo.Var(
    #     model.kapazitaet_index,
    #     domain=pyo.NonNegativeReals,
    #     bounds=lambda m, t, c: (
    #         df_parameter.loc[t, 'untere Kapagrenze [MWh]'],
    #         df_parameter.loc[t, 'obere Kapagrenze [MWh]']
    #     )
    # )
    return model

# definieren der Zielfunktion, wobei die Differenz aus der zu installierenden Leistung minus der bereits installierten Leistung (untere Grenze) gebildet wird und mit den Kosten multipliziert wird
def define_objective(model, df_parameter):
    def cost_rule(m):
        return sum(
            kosten[t] * (m.inst_leistung[t, c] - df_parameter.loc[t, 'untere Grenze [MW]'])
            for (t, c) in m.inst_leistung_index
        )
    model.objective = pyo.Objective(rule=cost_rule, sense=pyo.minimize)
    return model