#Hier wird Schritt für Schritt das Energiemodell und dessen Optimierung aufgebaut.
# Als erstes wird nur der Sektor Strom betrachtet. Erzeuger und Stromspeicher gleichen den Bedarf aus.
# Die Optimierung wird mit dem Paket Pyomo durchgeführt.

import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd

# Daten einlesen
from daten_einlesen import df_bedarf, df_erzeuger_strom, df_erzeuger_wärme
#ACHTUNG: df_bedarf addiert zu strom bereits wp und emob bedarf!

# Parameter laden
df_parameter = pd.read_excel(r'data\Optimierungsgrößen.xlsx', index_col=0)

#%%Variablenhandling

technologien = df_parameter.index.tolist()

#Energieträger-Attributzuordnung
traeger_dict = {t: df_parameter.loc[t, 'Energieträger'] for t in df_parameter.index}

energietraeger = list(set(traeger_dict.values()))

#Art-Attributzuordnung
art_dict = {t: df_parameter.loc[t, 'Art'] for t in df_parameter.index}

technologieart = list(set(art_dict.values()))

kosten = (df_parameter['Kosten'] * 1000).to_dict() #Kosten mal 1000 um von €/kW in €/MW zu konvertieren

# Nur die Spalten aus df_erzeuger_strom übernehmen, die auch im Index von df_parameter sind
gemeinsame_s_techs = [t for t in df_erzeuger_strom.columns if t in df_parameter.index and traeger_dict[t] == 'Strom']
df_erzeuger_strom = df_erzeuger_strom[gemeinsame_s_techs]

gemeinsame_wae_techs = [t for t in df_erzeuger_wärme.columns if t in df_parameter.index and traeger_dict[t] == 'Wärme']



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
    model.kapazitaet_index =[(t,c) for t in model.techs for c in model.traeger if art_dict[t] == 'Speicher' and traeger_dict[t] == c]
    model.kapazitaet = pyo.Var(
        model.kapazitaet_index,
        domain=pyo.NonNegativeReals,
        bounds=lambda m, t, c: (
            df_parameter.loc[t, 'untere Kapagrenze [MWh]'],
            df_parameter.loc[t, 'obere Kapagrenze [MWh]']
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
verf_s_dict = {}
verf_wae_dict = {}
# Nur Technologien verwenden, die sowohl in df_erzeuger_strom als auch in df_parameter vorhanden sind
gueltige_s_techs = [t for t in df_erzeuger_strom.columns if t in df_parameter.index]
for t in gueltige_s_techs:
    for ti in df_erzeuger_strom.index:
        verf_s_dict[(t, ti)] = df_erzeuger_strom.loc[ti, t]

#Nur Technologien verwenden, die sowohl in df_erzeuger_wärme als auch in df_parameter vorhanden sind
gueltige_wae_techs = [t for t in df_erzeuger_wärme.columns if t in df_parameter.index]
for t in gueltige_wae_techs:
    for ti in df_erzeuger_wärme.index:
        verf_wae_dict[(t, ti)] = df_erzeuger_wärme.loc[ti, t]


def define_constraints(model, df_bedarf):
    # Strombedarf als Parameter
    model.Strombedarf = pyo.Param(model.T, initialize=df_bedarf['Strom'].to_dict())
    model.Waermebedarf = pyo.Param(model.T, initialize=df_bedarf['Wärme'].to_dict())

    # Verfügbarkeit der Stromtechnologien als Parameter
    model.Verf_s = pyo.Param(model.techs, model.T, initialize=verf_s_dict, default=0)
    model.Verf_wae = pyo.Param(model.techs, model.T, initialize=verf_wae_dict, default=0)
    # Erzeugungsgleichung
    def strom_erzeuger_regel(m, time):
        stromerzeuger_summe = sum(
            m.inst_leistung[t,'Strom'] * m.Verf_s[t, time]
            for t in m.techs
            if m.art_map[t] == 'Erzeuger' and m.traeger_map[t] == 'Strom'
        ) 
        stromspeicher_summe = sum(
        m.stromspeicher_leistung[t, time]
        for t in m.techs
        if m.art_map[t] == 'Speicher' and m.traeger_map[t] == 'Strom'
    )
        return stromerzeuger_summe + stromspeicher_summe >= m.Strombedarf[time]
    
    model.strom_erzeuger_bedingung = pyo.Constraint(model.T, rule=strom_erzeuger_regel)
    

    def waerme_erzeuger_regel(m, time):
        waermeerzeuger_summe = sum(
            m.inst_leistung[t,'Wärme'] * m.Verf_wae[t, time]
            for t in m.techs
            if m.art_map[t] == 'Erzeuger' and m.traeger_map[t] == 'Wärme'
        )
        return waermeerzeuger_summe >= m.Waermebedarf[time]
    model.waerme_erzeuger_bedingung = pyo.Constraint(model.T, rule=waerme_erzeuger_regel)
    return model


def stromspeicher_regeln(model):
    # Stromspeichertechnologien identifizieren
    stromspeicher_techs = [
        t for t in model.techs 
        if model.art_map[t] == 'Speicher' and model.traeger_map[t] == 'Strom'
    ]

    # Speicherfüllstand als Variable
    model.stromspeicher_stand = pyo.Var(
        stromspeicher_techs, model.T,
        domain=pyo.NonNegativeReals,
        bounds=(0, None)  # Obergrenze wird per Constraint gesetzt
    )

    # Constraint: Speicherstand darf Kapazität nicht überschreiten
    def storage_level_constraint_rule(m, t, time):
        return m.stromspeicher_stand[t, time] <= m.kapazitaet[t, 'Strom']
    model.storage_level_constraint = pyo.Constraint(
        stromspeicher_techs, model.T,
        rule=storage_level_constraint_rule
    )

    # Lade-/Entladeleistung als Variable
    model.stromspeicher_leistung = pyo.Var(
    stromspeicher_techs, model.T,
    domain=pyo.Reals,
    bounds=(None, None)  # Keine festen Bounds, stattdessen Constraints
)

    def storage_power_constraint_lower(m, t, time):
        return m.stromspeicher_leistung[t, time] >= -m.inst_leistung[t, 'Strom']
    model.storage_power_constraint_lower = pyo.Constraint(
        stromspeicher_techs, model.T,
        rule=storage_power_constraint_lower
    )

    def storage_power_constraint_upper(m, t, time):
        return m.stromspeicher_leistung[t, time] <= m.inst_leistung[t, 'Strom']
    model.storage_power_constraint_upper = pyo.Constraint(
        stromspeicher_techs, model.T,
        rule=storage_power_constraint_upper
    )

    # Anfangsbedingung: Speicher zu Beginn halb voll (oder leer)
    model.stromspeicher_init = pyo.Constraint(
        stromspeicher_techs,
        rule=lambda m, t: m.stromspeicher_stand[t, m.T.first()] == 0.5 * m.kapazitaet[t, 'Strom']
    )

    # Speicherbilanz für jeden Zeitpunkt (außer dem ersten)
    def storage_balance_rule(m, t, time):
        if time == m.T.first():
            return pyo.Constraint.Skip
        # Find previous time index
        time_list = list(m.T.data() if hasattr(m.T, "data") else m.T)
        idx = time_list.index(time)
        prev_time = time_list[idx - 1]
        return m.stromspeicher_stand[t, time] == (
            m.stromspeicher_stand[t, prev_time] 
            + m.stromspeicher_leistung[t, prev_time]/4 #geitelt durch 4, da 15 Minuten Intervalle
        )
    model.storage_balance = pyo.Constraint(
        stromspeicher_techs, model.T,
        rule=storage_balance_rule
    )


    return model


def weitere_speicher_regeln(model):
    # Batteriespeicher sollen vor Pumpspeichern eingesetzt werden.
    # Es wird angenommen, dass die Technologiebezeichnungen "Batteriespeicher" und "Pumpspeicher" enthalten.
    # Außerdem wird verhindert, dass Speicher gleichzeitig laden und entladen (keine Leistungskreisläufe).

    # Batteriespeicher und Pumpspeicher identifizieren
    batterie_techs = [t for t in model.techs if "Batterie" in t and model.art_map[t] == 'Speicher']
    pumpspeicher_techs = [t for t in model.techs if "Pumpspeicher" in t and model.art_map[t] == 'Speicher']

    # Regel: Pumpspeicher dürfen nur entladen, wenn Batteriespeicher nicht mehr entladen können
    # (d.h. Batteriespeicherleistung ist ausgeschöpft)
    def pumpspeicher_nachrangig_rule(m, time):
        # Summe der Entladeleistung (negative Werte) der Batteriespeicher
        batterie_entladung = sum(
            -m.stromspeicher_leistung[t, time] for t in batterie_techs if (t, 'Strom') in m.kapazitaet_index
        )
        # Summe der Entladeleistung der Pumpspeicher
        pumpspeicher_entladung = sum(
            -m.stromspeicher_leistung[t, time] for t in pumpspeicher_techs if (t, 'Strom') in m.kapazitaet_index
        )
        # Pumpspeicher dürfen nur entladen, wenn Batteriespeicher voll ausgelastet sind
        # (Hier: Pumpspeicherentladung <= max. mögliche Batterieentladung - tatsächliche Batterieentladung)
        max_batterie_entladung = sum(
            m.inst_leistung[t, 'Strom'] for t in batterie_techs if (t, 'Strom') in m.inst_leistung_index
        )
        return pumpspeicher_entladung <= 1e-3 + max_batterie_entladung - batterie_entladung
    if batterie_techs and pumpspeicher_techs:
        model.pumpspeicher_nachrangig = pyo.Constraint(model.T, rule=pumpspeicher_nachrangig_rule)

    
    # Binäre Variablen zur Steuerung des Vorzeichens der Speicherleistung pro Zeitpunkt
    model.is_non_negative = pyo.Var(model.T, domain=pyo.Binary)  # 1, wenn alle Speicherleistungen >= 0 (Laden)
    model.is_non_positive = pyo.Var(model.T, domain=pyo.Binary)  # 1, wenn alle Speicherleistungen <= 0 (Entladen)
    M = 1e10  # große Konstante für Big-M-Methode

    # Constraint: Wenn is_non_negative[t] = 1, dann sind alle Speicherleistungen >= 0 (Laden)
    def all_non_negative_rule(m, t, tech):
        if m.art_map[tech] == 'Speicher' and m.traeger_map[tech] == 'Strom':
            return m.stromspeicher_leistung[tech, t] >= -M * (1 - m.is_non_negative[t])
        else:
            return pyo.Constraint.Skip

    # Constraint: Wenn is_non_positive[t] = 1, dann sind alle Speicherleistungen <= 0 (Entladen)
    def all_non_positive_rule(m, t, tech):
        if m.art_map[tech] == 'Speicher' and m.traeger_map[tech] == 'Strom':
            return m.stromspeicher_leistung[tech, t] <= M * (1 - m.is_non_positive[t])
        else:
            return pyo.Constraint.Skip

    # Constraint: Pro Zeitpunkt darf nur eine Richtung aktiv sein (Laden oder Entladen)
    def only_one_sign_rule(m, t):
        return m.is_non_negative[t] + m.is_non_positive[t] == 1

    # Constraints im Modell registrieren
    model.all_non_negative_constr = pyo.Constraint(model.T, model.techs, rule=all_non_negative_rule)
    model.all_non_positive_constr = pyo.Constraint(model.T, model.techs, rule=all_non_positive_rule)
    model.only_one_sign_constr = pyo.Constraint(model.T, rule=only_one_sign_rule)

    # Zusätzliche Variable: Batterie-Priorität (1, wenn Batterie am Limit)
    model.battery_priority = pyo.Var(model.T, domain=pyo.Binary)

    # Constraint: Mindestaktivierungsdauer für Pumpspeicher (z.B. 1 Stunde = 4 Intervalle)
    def pump_minimum_runtime(m, t):
        if t < m.T.last():
            # Index des aktuellen Zeitpunkts bestimmen
            time_list = list(m.T.data() if hasattr(m.T, "data") else m.T)
            idx = time_list.index(t)
            # Nächsten Zeitpunkt mit Mindestdauer bestimmen
            if hasattr(time_list[idx], 'freq') and time_list[idx].freq is not None:
                next_time = time_list[idx] + 3 * time_list[idx].freq
            else:
                # Fallback: 4. nächstes Element, falls freq nicht verfügbar
                if idx + 3 < len(time_list):
                    next_time = time_list[idx + 3]
                else:
                    return pyo.Constraint.Skip
            # Batterie-Priorität muss für Mindestdauer erhalten bleiben
            return m.battery_priority[t] <= m.battery_priority[next_time]
        return pyo.Constraint.Skip
    model.pump_min_runtime = pyo.Constraint(model.T, rule=pump_minimum_runtime)

    return model





#Funktion zum Lösen des Modells
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


# Hauptfunktion zum Erstellen und Lösen des Modells
def main():
    model = create_energy_system_model(df_bedarf) #Modell erstellen
    model = define_variables(model, df_parameter) #Variablen definieren
    model = define_objective(model, df_parameter) #Zielfunktion definieren
    model = stromspeicher_regeln(model) # Speicherregeln definieren
    model = define_constraints(model, df_bedarf) #Nebenbedingungen definieren
    model = weitere_speicher_regeln(model)
    
    
    solved_model = solve_model(model)
    return solved_model


print(df_erzeuger_strom[gemeinsame_s_techs].describe())
ergebnis_model = main()

#%% Ergebnisse auswerten
# Extrahiere Zeitreihen für alle Speichertechnologien und Zeitpunkte
stromspeicher_stand_values = {
    (t, time): pyo.value(ergebnis_model.stromspeicher_stand[t, time])
    for t in ergebnis_model.techs
    if (t, 'Strom') in ergebnis_model.kapazitaet_index  # Nur Speichertechnologien
    for time in ergebnis_model.T
    if ergebnis_model.stromspeicher_stand[t, time].value is not None
}

stromspeicher_leistung_values = {
    (t, time): pyo.value(ergebnis_model.stromspeicher_leistung[t, time])
    for t in ergebnis_model.techs
    if (t, 'Strom') in ergebnis_model.kapazitaet_index  # Nur Speichertechnologien
    for time in ergebnis_model.T
    if ergebnis_model.stromspeicher_leistung[t, time].value is not None
}

# Optional: Werte in DataFrames umwandeln
# Erstelle DataFrame: Index = Zeitpunkte, Spalten = Speichertechnologien, Werte = Speicherstand
df_stand = pd.DataFrame(
    {(t,): {time: val for (tech, time), val in stromspeicher_stand_values.items() if tech == t}
     for t in set(tech for (tech, _) in stromspeicher_stand_values.keys())}
)
# Spaltennamen anpassen: Technologie + '_stand'
df_stand.columns = [f"{t[0]}_stand" for t in df_stand.columns]

# Erstelle DataFrame: Index = Zeitpunkte, Spalten = Speichertechnologien, Werte = Speicherleistung
df_leistung = pd.DataFrame(
    {(t,): {time: val for (tech, time), val in stromspeicher_leistung_values.items() if tech == t}
     for t in set(tech for (tech, _) in stromspeicher_leistung_values.keys())}
)
df_leistung.columns = [f"{t[0]}_leistung" for t in df_leistung.columns] # Spaltennamen ohne Tuple
df_leistung.index.name = 'Zeitpunkt'
df_stand.index.name = 'Zeitpunkt'

df_leistung_stand = pd.concat([df_leistung, df_stand], axis=1)


# Extrahiere installierte Leistungen der Erzeugungstechnologien
installierte_leistungen = {
    (t, c): pyo.value(ergebnis_model.inst_leistung[t, c])
    for (t, c) in ergebnis_model.inst_leistung_index
    if ergebnis_model.inst_leistung[t, c].value is not None
}

# Multipliziere jede Spalte von df_erzeuger_strom mit der berechneten installierten Leistung der jeweiligen Technologie
df_Erzeugergang = df_erzeuger_strom.copy()
for t in df_Erzeugergang.columns:
    leistung = installierte_leistungen.get((t, 'Strom'), 0)
    df_Erzeugergang[t] = df_Erzeugergang[t] * leistung

#%%
print("Ende der Optimierung")