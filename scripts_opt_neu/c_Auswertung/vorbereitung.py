import pandas as pd

#Hier darzustellenden DataFrame importieren
opt_inst_Leistung = pd.read_excel(r'data\b_Optimierung\opt_inst_Leistung.xlsx', index_col=0, sheet_name='inst_leistung')

Batterie_zeitreihen = pd.read_excel(r'data\b_Optimierung\opt_speicher_zeitreihen.xlsx', index_col=0, sheet_name='Batteriespeicher_Batterie')
Pumpspeicher_zeitreihen = pd.read_excel(r'data\b_Optimierung\opt_speicher_zeitreihen.xlsx', index_col=0, sheet_name='Pumpspeicher_Pump')

bedarf_gesamt = pd.read_excel(r'data\b_Optimierung\Bedarfe_Gesamt_15min_2023.xlsx', index_col=0)

verfügbarkeiten_strom = pd.read_excel(r'data\b_Optimierung\Verfügbarkeiten_Stromerzeuger_15min_2023.xlsx', index_col=0)

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

opt_inst_Leistung_verfügbar.to_excel(r'data\c_Auswertung\opt_inst_Leistung_verfügbar.xlsx', index=True)

# Bedarf und Deckung zusammenführen

bedarf_deckung = opt_inst_Leistung_verfügbar.copy()

bedarf_deckung['Summe_Stromerzeugung [MW]'] = bedarf_deckung.sum(axis=1)

bedarf_deckung['Batterie_Leistung [MW]'] = Batterie_zeitreihen['Leistung [MW]']
bedarf_deckung['Pumpspeicher_Leistung [MW]'] = Pumpspeicher_zeitreihen['Leistung [MW]'].reindex(bedarf_deckung.index, method='ffill')

bedarf_deckung['Summe_Stromerzeugung [MW]'] += bedarf_deckung['Batterie_Leistung [MW]'] + bedarf_deckung['Pumpspeicher_Leistung [MW]']

bedarf_deckung['Strom_Gesamt_Bedarf [MW]'] = bedarf_gesamt['Strom_Gesamt_Bedarf [MW]']

bedarf_deckung['Deckungsgrad [%]'] = (bedarf_deckung['Summe_Stromerzeugung [MW]'] / bedarf_deckung['Strom_Gesamt_Bedarf [MW]']) * 100

print("Zeitpunkte mit Deckungsgrad < 100%:")
print(bedarf_deckung[bedarf_deckung['Deckungsgrad [%]'] < 100].index.tolist())

bedarf_deckung.to_excel(r'data\c_Auswertung\bedarf_deckung.xlsx', index=True)

print("Ende der vorbereitung.py Datei")
