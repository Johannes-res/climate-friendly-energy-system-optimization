import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd

# Daten einlesen
from daten_einlesen import df_bedarf, df_erzeuger_strom

# Parameter laden
df_parameter = pd.read_excel(r'data\Optimierungsgrößen.xlsx', index_col=0)

def create_energy_system_model(df_bedarf, df_erzeuger_strom, df_erzeuger_wärme):
    # Modell-Initialisierung
    model = pyo.ConcreteModel()
    
    # Zeitindex definieren
    model.T = pyo.Set(initialize=df_bedarf.index, ordered=True)
    
    return model

#Feste Werte definieren

kosten = (df_parameter['Kosten'] * 1000).to_dict()  # Kosten mal 1000 um von €/kW in €/MW zu konvertieren

effizienz = (df_parameter['Effizienz']).to_dict()  # Effizienz in Dezimalform


#Variablen definieren
def definiere_variablen(model):
    # Stromerzeuger-Kapazitäten
    model.es1 = pyo.Var(within=pyo.NonNegativeReals, bounds=(df_parameter.loc['Kernenergie','untere Grenze [MW]'],      df_parameter.loc['Kernenergie', 'obere Grenze [MW]']),      name='Kernenergie') # Kernenergie
    model.es2 = pyo.Var(within=pyo.NonNegativeReals, bounds=(df_parameter.loc['Laufwasser', 'untere Grenze [MW]'],      df_parameter.loc['Laufwasser', 'obere Grenze [MW]']),       name='Laufwasser')  # Laufwasser
    model.es3 = pyo.Var(within=pyo.NonNegativeReals, bounds=(df_parameter.loc['Biomasse', 'untere Grenze [MW]'],        df_parameter.loc['Biomasse', 'obere Grenze [MW]']),         name='Biomasse')  # Biomasse
    model.es4 = pyo.Var(within=pyo.NonNegativeReals, bounds=(df_parameter.loc['Geothermie', 'untere Grenze [MW]'],      df_parameter.loc['Geothermie', 'obere Grenze [MW]']),       name='Geothermie')  # Geothermie
    model.es5 = pyo.Var(within=pyo.NonNegativeReals, bounds=(df_parameter.loc['Müll', 'untere Grenze [MW]'],            df_parameter.loc['Müll', 'obere Grenze [MW]']),             name='Müll')  # Müll
    model.es6 = pyo.Var(within=pyo.NonNegativeReals, bounds=(df_parameter.loc['Wind_Offshore', 'untere Grenze [MW]'],   df_parameter.loc['Wind_Offshore', 'obere Grenze [MW]']),    name='Wind_Offshore')  # Wind Offshore
    model.es7 = pyo.Var(within=pyo.NonNegativeReals, bounds=(df_parameter.loc['Wind_Onshore', 'untere Grenze [MW]'],    df_parameter.loc['Wind_Onshore', 'obere Grenze [MW]']),     name='Wind_Onshore')  # Wind Onshore
    model.es8 = pyo.Var(within=pyo.NonNegativeReals, bounds=(df_parameter.loc['Solar', 'untere Grenze [MW]'],           df_parameter.loc['Solar', 'obere Grenze [MW]']),            name='Solar')  # Solar


def definiere_objective(model, kosten):
    # Ziel: Minimierung der Gesamtkosten
    erzeuger_kosten = (
        model.es1 * kosten['Kernenergie'] +
        model.es2 * kosten['Laufwasser'] +
        model.es3 * kosten['Biomasse'] +
        model.es4 * kosten['Geothermie'] +
        model.es5 * kosten['Müll'] +
        model.es6 * kosten['Wind_Offshore'] +
        model.es7 * kosten['Wind_Onshore'] +
        model.es8 * kosten['Solar']
    )
    model.objective = pyo.Objective(expr=erzeuger_kosten, sense=pyo.minimize)


def definiere_nebenbedingungen(model, df_bedarf, df_erzeuger_strom, t):
    # Nebenbedingungen für die Stromerzeugung
    def strombedarfsdeckung_regel(model, t):
        erzeugung = (
        model.es1 * df_erzeuger_strom.loc[t,'Kernenergie'] +
        model.es2 * df_erzeuger_strom.loc[t,'Laufwasser'] +
        model.es3 * df_erzeuger_strom.loc[t,'Biomasse'] +
        model.es4 * df_erzeuger_strom.loc[t,'Geothermie'] +
        model.es5 * df_erzeuger_strom.loc[t,'Müll'] +
        model.es6 * df_erzeuger_strom.loc[t,'Wind_Offshore'] +
        model.es7 * df_erzeuger_strom.loc[t,'Wind_Onshore'] +
        model.es8 * df_erzeuger_strom.loc[t,'Solar']
    )
        #hier können dann noch die speicher und die wandler ergänzt werden
        return erzeugung >= df_bedarf.loc[t, 'Strom']
    model.strombedarfsdeckung = pyo.Constraint(model.T, rule=strombedarfsdeckung_regel)
    

#Ergebnisse extrahieren
def ergebnisse_extrahieren(model, time_index):
    """
    Extrahierung der Optimierungsergebnisse
    """
    results = {}
    
    # Installierte Kapazitäten
    results['generator_capacities'] = {
        'Kernenergie': pyo.value(model.es1),
        'Laufwasser': pyo.value(model.es2),
        'Biomasse': pyo.value(model.es3),
        'Geothermie': pyo.value(model.es4),
        'Müll': pyo.value(model.es5),
        'Wind_Offshore': pyo.value(model.es6),
        'Wind_Onshore': pyo.value(model.es7),
        'Solar': pyo.value(model.es8)
    }

def lösen_der_optimierung(df_bedarf, df_erzeuger_strom):

    # Modell erstellen
    model = create_energy_system_model(df_bedarf, df_erzeuger_strom, None)

    # Variablen definieren
    definiere_variablen(model)

    # Zielfunktion definieren
    definiere_objective(model, kosten)
    # Nebenbedingungen definieren
    definiere_nebenbedingungen(model, df_bedarf, df_erzeuger_strom, model.T)

    # Solver initialisieren
    solver = SolverFactory('cbc')
    
    # Modell lösen
    result = solver.solve(model, tee=True)
    
    # Ergebnis anzeigen
    if result.solver.termination_condition == pyo.TerminationCondition.optimal:
        print("Optimale Lösung gefunden:")
        for v in model.component_objects(pyo.Var, active=True):
            print(f"{v.name}: {v.value}")
    else:
        print("Keine optimale Lösung gefunden.")

ergebnisse = lösen_der_optimierung(df_bedarf, df_erzeuger_strom)

print('Ende')
