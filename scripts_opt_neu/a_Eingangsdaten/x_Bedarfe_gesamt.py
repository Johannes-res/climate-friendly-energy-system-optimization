#Modellvariante = 'Grundmodell_'
#Modellvariante = 'energetische_Gebäudesanierung_' # faktor 0.70 bei raumwärme im raumwärmeskript geändert
#Modellvariante = 'Verkehrswende_' # Faktor 0.8 bei Flugverkehr und 0.9 bei Emob
#Modellvariante = 'Import_H2_E_Fuel_' # Wasserstoff und E-Fuelbedarf werden entfernt
Modellvariante = 'Erzeugervariation_WEA_on_'
import os
from pathlib import Path
import pandas as pd

# Wechsle zum Projekt-Root (2 Ebenen nach oben vom Skript)
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)
print(f"Working Directory: {os.getcwd()}")




from x_strombedarf_org import strom_last_23, strom_last_23_original
print("✓ strom_last_23 importiert")

# from x_emobbedarf import e_mob_bedarf
# print("✓ e_mob_bedarf importiert")

e_mob_bedarf = pd.read_excel(r'data\a_Eingangsdaten\Mobilität\EMob_Zeitreihe_15min_Jahr.xlsx')

# print("Importiere raumwärmebedarf (kann etwas dauern, da Wetterdaten geladen werden)...")
# from x_raumwärmebedarf import df_strom_15min as raumwärmebedarf
# print("✓ raumwärmebedarf importiert")

# print("Importiere warmwasserbedarf...")
# from x_warmwasserbedarf import df_15min as warmwasserbedarf
# print("✓ warmwasserbedarf importiert")

raumwärmebedarf = pd.read_excel(r'data\a_Eingangsdaten\Wärme\Grundmodell_Raumwärme_Strombedarf_15min_23.xlsx')
print("✓ raumwärmebedarf importiert")
warmwasserbedarf = pd.read_excel(r'data\a_Eingangsdaten\Wärme\Warmwasser_Strombedarf_15min_23.xlsx')
print("✓ warmwasserbedarf importiert")
prozesswärmebedarf = pd.read_excel(r'data\a_Eingangsdaten\Wärme\Prozesswärmebedarf_15min_23_weighted.xlsx')
print("✓ prozesswärmebedarf importiert")
#Gesamtbedarf berechnen

##% Strom
#Kopie von des Strombedarfes von 2023 erstellen (458TWh - Biomasse und Müll da kein Erweiterungspotential)
bedarf_gesamt = strom_last_23.copy()

#sicherstellen, dass der Index datetime ist
bedarf_gesamt.index = pd.to_datetime(bedarf_gesamt.index)
raumwärmebedarf.set_index(raumwärmebedarf.columns[0], inplace=True)
raumwärmebedarf.index = pd.to_datetime(raumwärmebedarf.index)
warmwasserbedarf.set_index(warmwasserbedarf.columns[0], inplace=True)
warmwasserbedarf.index = pd.to_datetime(warmwasserbedarf.index)
e_mob_bedarf.set_index(e_mob_bedarf.columns[0], inplace=True)
e_mob_bedarf.index = pd.to_datetime(e_mob_bedarf.index)
prozesswärmebedarf.set_index(prozesswärmebedarf.columns[0], inplace=True)
prozesswärmebedarf.index = pd.to_datetime(prozesswärmebedarf.index)

#E-Mobilitätsbedarf hinzufügen (261,05 TWh im Jahr)
bedarf_gesamt['E_Mob_Bedarf [MW]'] = e_mob_bedarf['Last_emob']*1000  # Umrechnung in MW #Faktor 0.9 für Verkehrswende

# Raumwärmebedarf hinzufügen (434,4TWh im Jahr)
bedarf_gesamt['Raumwärmebedarf [MW]'] = raumwärmebedarf['Strombedarf_Raumwärme [GW]']*1000  # Umrechnung in MW #energetische_Gebäudesanierung

#Warmwasserbedarf hinzufügen (80,7TWh im Jahr)
bedarf_gesamt['Warmwasserbedarf [MW]'] = warmwasserbedarf['Strombedarf_Warmwasser [GW]']*1000  # Umrechnung in MW

#Zu strom_last_23 noch eine Spalte mit dem gleichverteilenten zusätzlichen Jahresstrombedarf der Industrie und mech.Energie GHD hinzufügen
jahresstrombedarf_industrie = (400000-185900)+16500  # in GWh: Prognose - Bedarf 2023 + mech.Energie GHD (0,5 *32,2TWh durch elektrifizierung)
bedarf_gesamt['Industrie_Strom_Last [MW]'] = jahresstrombedarf_industrie * 1000 / (365 * 24 )  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle



#%% Wasserstoff der einzelnen Sektoren hinzufügen
#Wirkungsgrad für Elektrolyse
eta_elektrolyse = 0.65  # 65% Wirkungsgrad

#Wasserstoffbedarf Verkehr und Industrie (100,74 TWh im Jahr)
wasserstoff_verkehr_jahr = 7.74e3  # in GWh Schifffahrt und MIV       #*0 bei Import
wasserstoff_industrie_jahr = 93e3  # in GWh                           #*0 bei Import
bedarf_gesamt['Wasserstoffbedarf [MW]'] = (wasserstoff_industrie_jahr + wasserstoff_verkehr_jahr) * 1000 / (365 * 24 *eta_elektrolyse)  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle


#%% sonstige

# #mechanische Energie Gebäude hinzufügen
# mechanische_energie_gebäude_jahr = 32.2e3*0.5  # in GWh mit effizienzgewinn durch elektromotoren statt verbrennung (50% angenommen) wie bei Verkehr
# bedarf_gesamt['Mechanische_Energie_Gebäude [MW]'] = mechanische_energie_gebäude_jahr * 1000 / (365 * 24)  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle


# Prozesswärmebedarf Fernwärme-Industrie und GHD (40.5e3) mit konservativen, festen COP von 3
bedarf_gesamt['Prozesswärmebedarf [MW]'] = prozesswärmebedarf ['Prozesswärmebedarf [GW]'] * 1000/3  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle

#E-Fuelbedarf für Flugzeuge
e_fuel_flugzeuge_jahr = 111.66e3 /0.4 # in GWh mit Wirkungsgradannahme von 40% für Power-to-Liquid --> Verkehrswende: *0.8 #*0 bei Import
bedarf_gesamt['E_Fuel_Flugzeuge [MW]'] = e_fuel_flugzeuge_jahr * 1000 / (365 * 24)  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle






#Gesamtbedarf berechnen
bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'] = bedarf_gesamt.sum(axis=1)

bedarf_gesamt ['Strom_orginal_23 [MW]'] = strom_last_23_original['Last']
bedarf_gesamt.to_excel(f'data/b_Optimierung/{Modellvariante}Bedarfe_Gesamt_alles_Strom_15min_2023.xlsx', index=True)

   
#summen check

print('Summencheck der einzelnen Bedarfe in TWh:')
print(f"Strombedarf Original -Biomasse und Müll 2023: {bedarf_gesamt['Strom_Last [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"E-Mobilitätsbedarf 2023: {bedarf_gesamt['E_Mob_Bedarf [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Raumwärmebedarf 2023: {bedarf_gesamt['Raumwärmebedarf [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Warmwasserbedarf 2023: {bedarf_gesamt['Warmwasserbedarf [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Industrie Strombedarf 2023: {bedarf_gesamt['Industrie_Strom_Last [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Wasserstoffbedarf  2023: {bedarf_gesamt['Wasserstoffbedarf [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Prozesswärmebedarf 2023: {bedarf_gesamt['Prozesswärmebedarf [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"E-Fuel Bedarf Flugzeuge 2023: {bedarf_gesamt['E_Fuel_Flugzeuge [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Gesamtbedarf 2023: {bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Maximalwert Gesamtbedarf in MW: {bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'].max()/1000:.2f} GW zum Zeitpunkt {bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'].idxmax()}")
print(f"Minimalwert Gesamtbedarf in MW: {bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'].min()/1000:.2f} GW zum Zeitpunkt {bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'].idxmin()}")

# Save to Excel

summencheck_data = {
    'Kategorie': ['Strombedarf Original 2023- Biomasse und Müll', 'E-Mobilitätsbedarf 2023', 'Raumwärmebedarf 2023', 
                  'Warmwasserbedarf 2023', 'Industrie Strombedarf 2023', 'Wasserstoffbedarf 2023', 
                  'Prozesswärmebedarf 2023', 'E-Fuel Bedarf Flugzeuge 2023', 'Gesamtbedarf 2023',
                  'Max Gesamtbedarf [GW]', 'Max Zeitpunkt', 'Min Gesamtbedarf [GW]', 'Min Zeitpunkt'],
    'Wert [GWh]': [
        bedarf_gesamt['Strom_Last [MW]'].sum() / (1000 * 4),
        bedarf_gesamt['E_Mob_Bedarf [MW]'].sum() / (1000 * 4),
        bedarf_gesamt['Raumwärmebedarf [MW]'].sum() / (1000 * 4),
        bedarf_gesamt['Warmwasserbedarf [MW]'].sum() / (1000 * 4),
        bedarf_gesamt['Industrie_Strom_Last [MW]'].sum() / (1000 * 4),
        bedarf_gesamt['Wasserstoffbedarf [MW]'].sum() / (1000 * 4),
        bedarf_gesamt['Prozesswärmebedarf [MW]'].sum() / (1000 * 4),
        bedarf_gesamt['E_Fuel_Flugzeuge [MW]'].sum() / (1000 * 4),
        bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'].sum() / (1000 * 4),
        bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'].max() / 1000,
        str(bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'].idxmax()),
        bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'].min() / 1000,
        str(bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'].idxmin())
    ]
}
df_summencheck = pd.DataFrame(summencheck_data)
df_summencheck.to_excel( f'data/b_Optimierung/{Modellvariante}summencheck_Bedarfe_Gesamt_alles_Strom_15min_2023.xlsx',sheet_name='Summencheck', index=False)

print('Ende x_Bedarfe_gesamt.py')