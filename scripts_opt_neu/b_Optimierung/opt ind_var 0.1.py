#Hier wird Schritt für Schritt das Energiemodell und dessen Optimierung aufgebaut.
# Als erstes wird nur der Sektor Strom betrachtet. Nur die Erzeugertechnologien gleichen den Strombedarf aus.
# Die Optimierung wird mit dem Paket Pyomo durchgeführt.

"""nötige Eingaben:
- df_bedarf: DataFrame der eine Zeitreihe beinhaltet mit dem Bedarf an Strom  (Später kommt noch Mobilität und Wärme hinzu)
- df_erzeuger_strom: DataFrame der eine Zeitreihe beinhaltet mit den Verfügbarkeitsfaktoren der Erzeuger für Strom
- df_parameter: DataFrame der die Optimierungsparameter für die Technologien beinhaltet, wie Kosten, Kapazitätsgrenzen und Energieträger
"""

import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd

# Daten einlesen
#from a_Eingangsdaten.daten_einlesen import df_bedarf, df_erzeuger_strom

# Parameter laden
df_parameter = pd.read_excel(r'data\a_Eingangsdaten\Testdaten\Test2\test-Optimierungsgrößen-1stetig_teuer-2fluktual_billig.xlsx', index_col=0)

df_bedarf =  pd.read_excel(r'data\a_Eingangsdaten\Testdaten\Test2\testreihe-Bedarf-fluktual_passend_fluktual1_Strom_1Tag.xlsx', index_col=0)
df_erzeuger_strom = pd.read_excel(r'data\a_Eingangsdaten\Testdaten\Test2\testreihe-Erzeuger-Strom-1Tag-1stetig-2fluktual.xlsx', index_col=0)

#%%Variablenhandling

technologien = df_parameter.index.tolist()

#Energieträger-Attributzuordnung
traeger_dict = {t: df_parameter.loc[t, 'Energieträger'] for t in df_parameter.index}

energietraeger = list(set(traeger_dict.values()))

#Art-Attributzuordnung
art_dict = {t: df_parameter.loc[t, 'Art'] for t in df_parameter.index}

technologieart = list(set(art_dict.values()))

kosten = (df_parameter['Kosten [€/MW]'] ).to_dict() # Kosten als Dictionary für die Optimierung

# Nur die Spalten aus df_erzeuger_strom übernehmen, die auch im Index von df_parameter sind
gemeinsame_techs = [t for t in df_erzeuger_strom.columns if t in df_parameter.index]
df_erzeuger_strom = df_erzeuger_strom[gemeinsame_techs]



#%%Modell erstellen
# zudem wird aus dem Dataframe df_bedarf der Index als Set T extrahiert, der die Zeitpunkte für die Optimierung darstellt.
def create_energy_system_model(df_bedarf):
    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=df_bedarf.index, ordered=True)
    return model


def define_variables(model, df_parameter):
    # Sets für Technologien, Energieträger, Arten
    model.techs = pyo.Set(initialize=technologien, ordered=True)
    model.traeger = pyo.Set(initialize=energietraeger, ordered=True)
    model.art = pyo.Set(initialize=technologieart, ordered=True)

    # Dictionaries als Pyomo-Parameter (Mapping)
    model.traeger_map = pyo.Param(model.techs, initialize=traeger_dict, within=pyo.Any)
    model.art_map = pyo.Param(model.techs, initialize=art_dict, within=pyo.Any)
    
    # Indizierte Variable nur für gültige Technologie-Träger-Kombinationen
    model.inst_leistung_index = [(t, c) for t in model.techs for c in model.traeger if traeger_dict[t] == c]
    model.inst_leistung = pyo.Var(
        model.inst_leistung_index,
        domain=pyo.NonNegativeReals,
        bounds=lambda m, t, c: (
            df_parameter.loc[t, 'untere Grenze [MW]'],
            df_parameter.loc[t, 'obere Grenze [MW]']
        )
    )
    return model

#Zielfunktion
#die Summe der einzelnen Kosten für t in m.inst_leistung, also jede Technologie wird mit den Kosten der Technologie multipliziert
# und die Summe wird minimiert. Die untere Grenze wird als Bestand angesehen, welcher die Kosten nicht beeinflusst.
def define_objective(model, df_parameter):
    # Kostenparameter
    def cost_rule(m):
        return sum(
            kosten[t] * (m.inst_leistung[t, c] - df_parameter.loc[t, 'untere Grenze [MW]'])
            for (t, c) in m.inst_leistung_index
        )
    model.objective = pyo.Objective(rule=cost_rule, sense=pyo.minimize)
    return model


# Nebenbedingungen/Einschränkungen

# Vor define_constraints():
verf_dict = {}
# Nur Technologien verwenden, die sowohl in df_erzeuger_strom als auch in df_parameter vorhanden sind
gueltige_techs = [t for t in df_erzeuger_strom.columns if t in df_parameter.index]
for t in gueltige_techs:
    for ti in df_erzeuger_strom.index:
        verf_dict[(t, ti)] = df_erzeuger_strom.loc[ti, t]


def define_constraints(model, df_bedarf):
    # Strombedarf als Parameter
    model.Strombedarf = pyo.Param(model.T, initialize=df_bedarf['Strom [MW]'].to_dict())

    # Verfügbarkeit der Technologien als Parameter
    model.Verf = pyo.Param(model.techs, model.T, initialize=verf_dict, default=0)
    # Erzeugungsgleichung
    def generation_constraint_rule(m, time):
        return sum(
            m.inst_leistung[t,'Strom'] * m.Verf[t, time]
            for t in m.techs
            if m.art_map[t] == 'Erzeuger' and m.traeger_map[t] == 'Strom'
        ) >= m.Strombedarf[time]
    
    model.generation_constraint = pyo.Constraint(model.T, rule=generation_constraint_rule)
    return model

def solve_model(model):
    solver = SolverFactory('cbc')  # oder 'glpk'
    results = solver.solve(model, tee=True)
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print("Optimale Lösung gefunden:")
        for (t, c) in model.inst_leistung_index:
            print(f"{t} ({c}): {pyo.value(model.inst_leistung[t, c]/1000):.2f} GW")
            print(f"Kosten für {t}: {pyo.value(kosten[t] * (model.inst_leistung[t, c] - df_parameter.loc[t, 'untere Grenze [MW]'])):.2f} Euro")
        print(f"Gesamtkosten: {pyo.value(model.objective):.2f} Euro")
    else:
        print("Keine optimale Lösung gefunden.")
    return model

def main():
    model = create_energy_system_model(df_bedarf)
    model = define_variables(model, df_parameter)
    model = define_objective(model, df_parameter)
    model = define_constraints(model, df_bedarf)
    solved_model = solve_model(model)
    return solved_model


print(df_erzeuger_strom[gemeinsame_techs].describe())
ergebnis_model = main()
print("Ende der Optimierung")