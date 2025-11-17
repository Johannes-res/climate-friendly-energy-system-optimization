import pandas as pd
import pyomo.environ as pyo

# Funktion zum Speichern der Ergebnisse
def speichere_ergebnisse(model):
    results = {}
    for v in model.component_objects(pyo.Var, active=True):
        var_name = v.getname()
        results[var_name] = {}
        for index in v:
            results[var_name][index] = pyo.value(v[index])
    
    # Alle Daten speichern
    with pd.ExcelWriter(r'data\b_Optimierung\opt_inst_Leistung.xlsx') as writer:
        for var_name, data in results.items():
            df = pd.DataFrame.from_dict(data, orient='index', columns=['opt_inst_Leistung [MW]'])
            # Spalten für Technologie und Träger aus dem Index extrahieren
            df['Technologie'] = df.index.str[0]
            df['Träger'] = df.index.str[1]
            df = df[['Technologie', 'Träger', 'opt_inst_Leistung [MW]']]
            df = df.set_index('Technologie')
            df.to_excel(writer, sheet_name=var_name[:31])  # Excel-Limit: 31 Zeichen
        

    
  
    
    return results