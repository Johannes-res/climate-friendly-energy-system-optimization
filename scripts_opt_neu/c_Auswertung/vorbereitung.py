#Modellvariante = 'Grundmodell_'
#Modellvariante = 'energetische_Gebäudesanierung_'
#Modellvariante = 'Verkehrswende_'
#Modellvariante = 'Basisjahr_2023_'
Modellvariante = 'Test2_'
Jahr = 2022
import pandas as pd

import os
from pathlib import Path

# Wechsle zum Projekt-Root (2 Ebenen nach oben vom Skript)
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)
print(f"Working Directory: {os.getcwd()}")
#Hier darzustellenden DataFrame importieren
opt_inst_Leistung = pd.read_excel(f'data/b_Optimierung/{Modellvariante}opt_inst_Leistung.xlsx', index_col=0, sheet_name='inst_leistung')

#Batterie_zeitreihen = pd.read_excel(f'data/b_Optimierung/{Modellvariante}opt_speicher_zeitreihen.xlsx', index_col=0, sheet_name='Batteriespeicher_Batterie')
#Pumpspeicher_zeitreihen = pd.read_excel(f'data/b_Optimierung/{Modellvariante}opt_speicher_zeitreihen.xlsx', index_col=0, sheet_name='Pumpspeicher_Pump')
#H2_speicher_zeitreihen = pd.read_excel(f'data/b_Optimierung/{Modellvariante}opt_speicher_zeitreihen.xlsx', index_col=0, sheet_name='Wasserstoffkaverne_H2')

#bedarf_gesamt = pd.read_excel(f'data/b_Optimierung/{Modellvariante}Bedarfe_Gesamt_alles_Strom_15min_{Jahr}.xlsx', index_col=0)
bedarf_gesamt = pd.read_excel(rf'data\a_Eingangsdaten\Testdaten\Test2\testreihe-Bedarf-fluktual_passend_fluktual1_Strom_1Tag.xlsx', index_col=0)

#verfügbarkeiten_strom = pd.read_excel(rf'data/b_Optimierung/Verfügbarkeiten_Stromerzeuger_15min_{Jahr}.xlsx', index_col=0)
verfügbarkeiten_strom = pd.read_excel(rf'data\a_Eingangsdaten\Testdaten\Test2\testreihe-Erzeuger-Strom-1Tag-1stetig-2fluktual.xlsx', index_col=0)

#DataFrame für Auswertung vorbereiten
# Verfügbarkeitsfaktoren werden mit optimierten installierten Leistungen multipliziert

def apply_availability(opt_inst_Leistung, verfügbarkeiten_strom):
    result = verfügbarkeiten_strom.copy()
    for tech in result.columns:
        if tech in opt_inst_Leistung.index:
            leistung = opt_inst_Leistung.loc[tech, 'Wert']
            result[tech] = result[tech] * leistung
        else:
            result.drop(tech, axis=1, inplace=True)
    return result

opt_inst_Leistung_verfügbar = apply_availability(opt_inst_Leistung, verfügbarkeiten_strom)

opt_inst_Leistung_verfügbar.to_excel(f'data/c_Auswertung/{Modellvariante}opt_inst_Leistung_verfügbar.xlsx', index=True)

# Bedarf und Deckung zusammenführen

bedarf_deckung = opt_inst_Leistung_verfügbar.copy()

bedarf_deckung['Summe_Stromerzeugung [MW]'] = bedarf_deckung.sum(axis=1)

#bedarf_deckung['Batterie_Leistung [MW]'] = Batterie_zeitreihen['Leistung [MW]']
#bedarf_deckung['Pumpspeicher_Leistung [MW]'] = Pumpspeicher_zeitreihen['Leistung [MW]'].reindex(bedarf_deckung.index, method='ffill')
#bedarf_deckung['H2_Speicher_Leistung [MW]'] = H2_speicher_zeitreihen['Leistung [MW]'].reindex(bedarf_deckung.index, method='ffill')

#bedarf_deckung['Summe_Stromerz+speicher [MW]'] = bedarf_deckung['Summe_Stromerzeugung [MW]'] + bedarf_deckung['Batterie_Leistung [MW]'] + bedarf_deckung['Pumpspeicher_Leistung [MW]'] + bedarf_deckung['H2_Speicher_Leistung [MW]']

bedarf_deckung['Strom_Gesamt_Bedarf [MW]'] = bedarf_gesamt['Strom_Gesamt_Bedarf [MW]']


#bedarf_deckung['Deckungsgrad [%]'] = (bedarf_deckung['Summe_Stromerz+speicher [MW]'] / bedarf_deckung['Strom_Gesamt_Bedarf [MW]']) * 100

#bedarf_deckung['Summe_Speicher_Leistung [MW]'] = bedarf_deckung['Batterie_Leistung [MW]'] + bedarf_deckung['Pumpspeicher_Leistung [MW]'] + bedarf_deckung['H2_Speicher_Leistung [MW]']

print("Zeitpunkte mit Deckungsgrad < 100%:")
#print(bedarf_deckung[bedarf_deckung['Deckungsgrad [%]'] < 99.999].index.tolist())

bedarf_deckung.to_excel(f'data/c_Auswertung/{Modellvariante}bedarf_deckung.xlsx', index=True)

#Maximum der Stromerzeugung und Speicherleistung ermitteln
# max_speicher_werte = pd.DataFrame({
#     'Metrik': [
#         'Max Stromerzeugung [MW]',
#         'Min Stromerzeugung [MW]',
#         'Max Speicherleistung [MW]',
#         'Min Speicherleistung [MW]',
#         'Max Pumpspeicher [MW]',
#         'Min Pumpspeicher [MW]',
#         'Max H2-Speicher [MW]',
#         'Min H2-Speicher [MW]',
#         'Max Batterie [MW]',
#         'Min Batterie [MW]'
#     ],
#     'Wert': [
#         bedarf_deckung['Summe_Stromerzeugung [MW]'].max(),
#         bedarf_deckung['Summe_Stromerzeugung [MW]'].min(),
#         bedarf_deckung['Summe_Speicher_Leistung [MW]'].max(),
#         bedarf_deckung['Summe_Speicher_Leistung [MW]'].min(),
#         bedarf_deckung['Pumpspeicher_Leistung [MW]'].max(),
#         bedarf_deckung['Pumpspeicher_Leistung [MW]'].min(),
#         bedarf_deckung['H2_Speicher_Leistung [MW]'].max(),
#         bedarf_deckung['H2_Speicher_Leistung [MW]'].min(),
#         bedarf_deckung['Batterie_Leistung [MW]'].max(),
#         bedarf_deckung['Batterie_Leistung [MW]'].min()
#     ],
#     'Zeitpunkt': [
#         bedarf_deckung['Summe_Stromerzeugung [MW]'].idxmax(),
#         bedarf_deckung['Summe_Stromerzeugung [MW]'].idxmin(),
#         bedarf_deckung['Summe_Speicher_Leistung [MW]'].idxmax(),
#         bedarf_deckung['Summe_Speicher_Leistung [MW]'].idxmin(),
#         bedarf_deckung['Pumpspeicher_Leistung [MW]'].idxmax(),
#         bedarf_deckung['Pumpspeicher_Leistung [MW]'].idxmin(),
#         bedarf_deckung['H2_Speicher_Leistung [MW]'].idxmax(),
#         bedarf_deckung['H2_Speicher_Leistung [MW]'].idxmin(),
#         bedarf_deckung['Batterie_Leistung [MW]'].idxmax(),
#         bedarf_deckung['Batterie_Leistung [MW]'].idxmin()
#     ]
# })

# max_speicher_werte.to_excel(f'data/c_Auswertung/{Modellvariante}Auswertung.xlsx', index=False)


print("Ende der vorbereitung.py Datei")
