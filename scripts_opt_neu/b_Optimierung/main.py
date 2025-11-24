import os
from pathlib import Path

# Wechsle zum Projekt-Root (2 Ebenen nach oben vom Skript)
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)
print(f"Working Directory: {os.getcwd()}")


import a_inputs as a_inputs
import b_model_structure as b_model_structure
import c_storage_constraints as c_storage_constraints
import c_constraints as c_constraints

import d_solver as d_solver
import pyomo.environ as pyo
try:
    from pyomo.contrib.infeasible import identify_infeasible_constraints
except ImportError:
    identify_infeasible_constraints = None


from f_speichern import speichere_ergebnisse

def debug_print_model_info(model):
    """Zeigt Modellstruktur ohne Werte anzuzeigen (vor dem Lösen)"""
    print("\n=== MODEL STRUCTURE DEBUG ===")
    
    # Guard against None or invalid model to avoid AttributeError
    if model is None or not hasattr(model, 'component_objects'):
        print("Model is None or does not provide component_objects(); skipping detailed debug.")
        return

    # Sets
    for s in model.component_objects(pyo.Set):
        print(f"Set {s.name}: {len(s)} elements")
        if len(s) < 20:  # Nur kleine Sets vollständig anzeigen
            print(f"  Elements: {list(s)}")
    
    # Variables
    for v in model.component_objects(pyo.Var):
        print(f"Variable {v.name}: {len(v)} elements")
        if hasattr(v, 'bounds') and callable(v.bounds):
            try:
                first_key = next(iter(v.keys()))
                bounds = v[first_key].bounds
                print(f"  Bounds example: {bounds}")
            except:
                print(f"  Bounds: N/A")
    
    # Parameters
    for p in model.component_objects(pyo.Param):
        print(f"Parameter {p.name}: {len(p)} elements")
    
    # Constraints
    for c in model.component_objects(pyo.Constraint):
        print(f"Constraint {c.name}: {len(c)} elements")
    
    # Summary
    print(f"\nModel Summary:")
    print(f"  Sets: {len(list(model.component_objects(pyo.Set)))}")
    print(f"  Variables: {len(list(model.component_objects(pyo.Var)))}")
    print(f"  Parameters: {len(list(model.component_objects(pyo.Param)))}")
    print(f"  Constraints: {len(list(model.component_objects(pyo.Constraint)))}")
    
    # Check capacity vs demand
    try:
        max_demand = a_inputs.df_bedarf['Strom_Gesamt_Bedarf [MW]'].max()
        total_capacity = a_inputs.df_parameter['obere Grenze [MW]'].sum()
        print(f"  Max Demand: {max_demand:.2f} MW")
        print(f"  Total Capacity: {total_capacity:.2f} MW")
        print(f"  Capacity Ratio: {total_capacity/max_demand:.2f}")
    except Exception as e:
        print(f"  Capacity check failed: {e}")

def main():
    model = b_model_structure.create_energy_system_model(a_inputs.df_bedarf)
    model = b_model_structure.define_variables(model, a_inputs.df_parameter)
    model = b_model_structure.define_objective(model, a_inputs.df_parameter)
    model = c_storage_constraints.stromspeicher_regeln(model)
    #model = c_storage_constraints.weitere_speicher_regeln(model)
    model = c_constraints.define_constraints(model, a_inputs.df_bedarf)
    
    debug_print_model_info(model)
    
    solved_model = d_solver.solve_model(model)
    return solved_model

ergebnis_model = main()

results= speichere_ergebnisse(ergebnis_model)

# if identify_infeasible_constraints is not None:
#     bad = list(identify_infeasible_constraints(ergebnis_model, tol=1e-6))
#     for c in bad[:50]:
#         print(c.local_name, c.body(), c.lower(), c.upper())
# else:
#     print("Warning: identify_infeasible_constraints not available")



# from pyomo.environ import Var, Constraint
# unused = []
# for v in b_model_structure.model.component_data_objects(Var, active=True):
#     # Kompakter Test: Variable kommt in mindestens einer Constraint zu stehen?
#     used = any(v is term for c in b_model_structure.model.component_data_objects(Constraint) for term in (c.body, c.lower, c.upper) )
#     if not used:
#         unused.append(v)
# print("Unbenutzte Variablen (Beispiele):", unused[:20])


print("Ende der main.py Datei")