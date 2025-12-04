import pyomo.environ as pyo
from a_inputs import technologien, energietraeger, technologieart, traeger_dict, art_dict, kosten, lebensdauer
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
    # model.kapazitaet_index = [(t, traeger_dict[t]) for t in model.techs if art_dict[t] == 'Speicher']
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
# Annualisierte CAPEX-Kostenrechnung mit Capital Recovery Factor (CRF)
def define_objective(model, df_parameter):
    """
    Zielfunktion: Minimiere annualisierte Investitionskosten (CAPEX)
    
    Formel: Annualisierte Kosten = CAPEX × CRF
    
    CRF (Capital Recovery Factor) = r × (1+r)^n / ((1+r)^n - 1)
    wobei:
    - r = Zinssatz (WACC, z.B. 0.05 = 5%)
    - n = Lebensdauer [Jahre]
    
    Für r=0 (keine Diskontierung): CRF = 1/n
    """
    
    # Zinssatz (Weighted Average Cost of Capital)
    WACC = 0.05  # 5% Standard für Energieprojekte
    
    def calculate_crf(lifetime, wacc=WACC):
        """Berechnet Capital Recovery Factor"""
        if wacc == 0:
            return 1.0 / lifetime
        else:
            return (wacc * (1 + wacc)**lifetime) / ((1 + wacc)**lifetime - 1)
    
    def cost_rule(m):
        total_cost = 0
        
        for (t, c) in m.inst_leistung_index:
            # Investitionskosten für neu installierte Leistung
            capex = kosten[t] * (m.inst_leistung[t, c] - df_parameter.loc[t, 'untere Grenze [MW]'])
            
            # Capital Recovery Factor basierend auf Lebensdauer
            lifetime = lebensdauer[t]
            crf = calculate_crf(lifetime, WACC)
            
            # Annualisierte Kosten
            annualized_cost = capex * crf
            
            total_cost += annualized_cost
        
        return total_cost
    
    model.objective = pyo.Objective(rule=cost_rule, sense=pyo.minimize)
    
    print("\n✓ Zielfunktion: Annualisierte CAPEX mit CRF")
    print(f"  WACC: {WACC*100:.1f}%")
    print(f"  Beispiel-CRF (25 Jahre): {calculate_crf(25, WACC):.4f}")
    print(f"  Beispiel-CRF (15 Jahre): {calculate_crf(15, WACC):.4f}")
    print(f"  Beispiel-CRF (60 Jahre): {calculate_crf(60, WACC):.4f}")

        
    return model

print('Ende b_model_structure.py')