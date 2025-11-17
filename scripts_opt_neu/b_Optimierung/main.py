import a_inputs as a_inputs
import b_model_structure as b_model_structure
import c_constraints as c_constraints
import d_solver as d_solver
# try:
#     from pyomo.contrib.infeasible import identify_infeasible_constraints
# except ImportError:
#     identify_infeasible_constraints = None


from f_speichern import speichere_ergebnisse


def main():
    model = b_model_structure.create_energy_system_model(a_inputs.df_bedarf)
    model = b_model_structure.define_variables(model, a_inputs.df_parameter)
    model = b_model_structure.define_objective(model, a_inputs.df_parameter)
    #model = c_constraints.stromspeicher_regeln(model)
    model = c_constraints.define_constraints(model, a_inputs.df_bedarf)
    #model = c_constraints.weitere_speicher_regeln(model)
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