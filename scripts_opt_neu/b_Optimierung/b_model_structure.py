import pyomo.environ as pyo
import pandas as pd
from a_inputs import technologien, energietraeger, technologieart, traeger_dict, art_dict, kosten, lebensdauer

def create_energy_system_model(df_bedarf, df_bedarf_daily):
    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=df_bedarf.index, ordered=True)
    time_daily = pd.to_datetime(df_bedarf_daily.index).date
    model.T_daily = pyo.Set(initialize=time_daily)

    time_list = list(model.T)
    time_hourly = time_list[::4]
    model.T_hourly = pyo.Set(initialize=time_hourly)
    print(f"✓ T_hourly erstellt: {len(time_hourly)} stündliche Zeitschritte")
    return model

def define_variables(model, df_parameter):
    model.techs = pyo.Set(initialize=technologien, ordered=True)
    model.traeger = pyo.Set(initialize=energietraeger, ordered=True)
    model.art = pyo.Set(initialize=technologieart, ordered=True)
    
    model.traeger_map = pyo.Param(model.techs, initialize=traeger_dict, within=pyo.Any)
    model.art_map = pyo.Param(model.techs, initialize=art_dict, within=pyo.Any)
    
    # ✅ Wirkungsgrade als Dictionary (für bounds-Berechnung)
    wirkungsgrade = (df_parameter['Wirkungsgrad']).to_dict()
    
    # Installierte Leistung
    model.inst_leistung_index = [(t, c) for t in model.techs for c in model.traeger if traeger_dict[t] == c]
    
    if len(model.inst_leistung_index) != len(set(model.inst_leistung_index)):
        duplicates = [item for item in model.inst_leistung_index if model.inst_leistung_index.count(item) > 1]
        print(f"⚠ WARNUNG: Duplikate in inst_leistung_index gefunden: {set(duplicates)}")
        model.inst_leistung_index = list(set(model.inst_leistung_index))
    
    print(f"✓ inst_leistung_index: {len(model.inst_leistung_index)} Einträge")
    
    model.inst_leistung = pyo.Var(
        model.inst_leistung_index,
        domain=pyo.NonNegativeReals,
        bounds=lambda m, t, c: (
            df_parameter.loc[t, 'untere Grenze [MW]'],
            df_parameter.loc[t, 'obere Grenze [MW]']
        )
    )
    
    # ✅ KORREKTUR: Wandler-Output mit FESTEN Bounds (aus df_parameter)
    wandler_techs = [t for t in model.techs if art_dict[t] == 'Wandler']
    
    if wandler_techs:
        # ✅ Berechne maximale Output-Leistung als KONSTANTE
        # Max. Output = Obere Grenze [MW] × Wirkungsgrad
        wandler_max_output = {}
        for t in wandler_techs:
            eta = wirkungsgrade.get(t, 1.0)
            max_input = df_parameter.loc[t, 'obere Grenze [MW]']
            max_output = max_input * eta
            wandler_max_output[t] = max_output
        
        # Output-Leistung [MW] (das, was rauskommt)
        model.wandler_output = pyo.Var(
            [(t, time) for t in wandler_techs for time in model.T],
            domain=pyo.NonNegativeReals,
            bounds=lambda m, t, time: (0, wandler_max_output[t])  # ← KONSTANT!
        )
        
        print(f"✓ Wandler-Output-Variable erstellt: {len(wandler_techs)} Technologien × {len(list(model.T))} Zeitschritte")
        print(f"  Wandler-Technologien und Max-Output:")
        for t in wandler_techs:
            eta = wirkungsgrade.get(t, 1.0)
            max_input = df_parameter.loc[t, 'obere Grenze [MW]']
            max_output = wandler_max_output[t]
            print(f"    - {t}: η = {eta:.2f}, Max Input = {max_input:.0f} MW, Max Output = {max_output:.0f} MW")
    
    # ✅ WICHTIG: Füge Constraint hinzu, dass wandler_output durch TATSÄCHLICHE inst_leistung begrenzt ist
    if wandler_techs:
        def wandler_output_kapazitaet_regel(m, t, time):
            """Verknüpft wandler_output mit der tatsächlich installierten Leistung"""
            eta = wirkungsgrade.get(t, 1.0)
            # Output ≤ installierte Input-Leistung × Wirkungsgrad
            return m.wandler_output[t, time] <= m.inst_leistung[t, traeger_dict[t]] * eta
        
        model.wandler_output_kapazitaet = pyo.Constraint(
            [(t, time) for t in wandler_techs for time in model.T],
            rule=wandler_output_kapazitaet_regel
        )
        print(f"  ✓ Wandler-Output-Kapazitäts-Constraint hinzugefügt ({len(wandler_techs)} × {len(list(model.T))} = {len(wandler_techs) * len(list(model.T))} Constraints)")
    
    return model

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