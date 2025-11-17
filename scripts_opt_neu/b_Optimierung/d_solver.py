import pyomo.environ as pyo
from pyomo.opt import SolverFactory
from scripts_opt_neu.b_Optimierung.a_inputs import kosten, df_parameter

def solve_model(model):
    solver = SolverFactory('cbc')  # oder 'glpk'
    results = solver.solve(model, tee=True)
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print("Optimale Lösung gefunden:")
        for (t, c) in model.inst_leistung_index:
            print(f"{t} ({c}): {pyo.value(model.inst_leistung[t, c] / 1000):.2f} GW")
            print(f"Kosten für {t}: {pyo.value(kosten[t] * (model.inst_leistung[t, c] - df_parameter.loc[t, 'untere Grenze [MW]'])):.2f} Euro")
        print(f"Gesamtkosten: {pyo.value(model.objective):.2f} Euro")
    else:
        print("Keine optimale Lösung gefunden.")
    return model

print("Ende der solver.py Datei")