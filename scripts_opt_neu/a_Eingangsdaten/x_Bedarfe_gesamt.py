import os
from pathlib import Path

# Wechsle zum Projekt-Root (2 Ebenen nach oben vom Skript)
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)
print(f"Working Directory: {os.getcwd()}")




from x_strombedarf_org import strom_last_23
print("✓ strom_last_23 importiert")

from x_emobbedarf import e_mob_bedarf
print("✓ e_mob_bedarf importiert")

import pandas as pd

print("Importiere raumwärmebedarf (kann etwas dauern, da Wetterdaten geladen werden)...")
from x_raumwärmebedarf import df_strom_15min as raumwärmebedarf
print("✓ raumwärmebedarf importiert")

print("Importiere warmwasserbedarf...")
from x_warmwasserbedarf import df_15min as warmwasserbedarf
print("✓ warmwasserbedarf importiert")

# raumwärmebedarf = pd.read_excel(r'data\a_Eingangsdaten\Wärme\Raumwärme_Strombedarf_15min_23.xlsx')
# warmwasserbedarf = pd.read_excel(r'data\a_Eingangsdaten\Wärme\Warmwasser_Strombedarf_15min_23.xlsx')

#Gesamtbedarf berechnen

##% Strom
#Kopie von des Strombedarfes von 2023 erstellen
bedarf_gesamt = strom_last_23.copy()

#E-Mobilitätsbedarf hinzufügen (261,05 TWh im Jahr)
bedarf_gesamt['E_Mob_Bedarf [MW]'] = e_mob_bedarf*1000  # Umrechnung in MW

# Raumwärmebedarf hinzufügen hier noch COP-WP einbauen (431TWh im Jahr)
bedarf_gesamt['Raumwärmebedarf [MW]'] = raumwärmebedarf['Strombedarf_Raumwärme [GW]']*1000  # Umrechnung in MW

#Warmwasserbedarf hinzufügen (80TWh im Jahr)
bedarf_gesamt['Warmwasserbedarf [MW]'] = warmwasserbedarf['Strombedarf_Warmwasser [GW]']*1000  # Umrechnung in MW

#Zu strom_last_23 noch eine Spalte mit dem gleichverteilenten Jahresstrombedarf der Industrie hinzufügen
jahresstrombedarf_industrie = 400000  # in GWh
bedarf_gesamt['Industrie_Strom_Last [MW]'] = jahresstrombedarf_industrie * 1000 / (365 * 24 )  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle



#%% Wasserstoff der einzelnen Sektoren hinzufügen
#Wirkungsgrad für Elektrolyse
eta_elektrolyse = 0.65  # 65% Wirkungsgrad

#Wasserstoffbedarf Verkehr
wasserstoff_verkehr_jahr = 7.38e3  # in GWh Schifffahrt und MIV
bedarf_gesamt['Wasserstoff_Verkehr [MW]'] = wasserstoff_verkehr_jahr * 1000 / (365 * 24 *eta_elektrolyse)  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle

#Wasserstoffbedarf Industrie
wasserstoff_industrie_jahr = 93e3  # in GWh
bedarf_gesamt['Wasserstoff_Industrie [MW]'] = wasserstoff_industrie_jahr * 1000 / (365 * 24 *eta_elektrolyse)  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle


#%% sonstige

#mechanische Energie Gebäude hinzufügen
mechanische_energie_gebäude_jahr = 32.2e3*0.5  # in GWh mit effizienzgewinn durch elektromotoren statt verbrennung (50% angenommen) wie bei Verkehr
bedarf_gesamt['Mechanische_Energie_Gebäude [MW]'] = mechanische_energie_gebäude_jahr * 1000 / (365 * 24)  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle

# fernwärmebedarf Industrie hinzufügen # Hier auch noch COP mit einfließen lassen? sonst erstmal mit starren faktor von 3 rechnen?
fernwaerme_industrie_jahr = 40e3/3  # in GWh
bedarf_gesamt['Fernwärme_Industrie [MW]'] = fernwaerme_industrie_jahr * 1000 / (365 * 24)  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle

#E-Fuelbedarf für Flugzeuge
e_fuel_flugzeuge_jahr = 111.66e3 /0.17 # in GWh mit Wirkungsgradannahme von 17% für Power-to-Liquid

bedarf_gesamt['E_Fuel_Flugzeuge [MW]'] = e_fuel_flugzeuge_jahr * 1000 / (365 * 24)  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle






#Gesamtbedarf berechnen
bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'] = bedarf_gesamt.sum(axis=1)

bedarf_gesamt.to_excel(r'data\b_Optimierung\Bedarfe_Gesamt_alles_Strom_15min_2023.xlsx', index=True)

#summen check
print('Summencheck der einzelnen Bedarfe in TWh:')
print(f"Strombedarf Original 2023: {strom_last_23['Strom_Last [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"E-Mobilitätsbedarf 2023: {bedarf_gesamt['E_Mob_Bedarf [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Raumwärmebedarf 2023: {bedarf_gesamt['Raumwärmebedarf [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Warmwasserbedarf 2023: {bedarf_gesamt['Warmwasserbedarf [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Industrie Strombedarf 2023: {bedarf_gesamt['Industrie_Strom_Last [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Wasserstoffbedarf Verkehr 2023: {bedarf_gesamt['Wasserstoff_Verkehr [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Wasserstoffbedarf Industrie 2023: {bedarf_gesamt['Wasserstoff_Industrie [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Mechanische Energie Gebäude 2023: {bedarf_gesamt['Mechanische_Energie_Gebäude [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Fernwärmebedarf Industrie 2023: {bedarf_gesamt['Fernwärme_Industrie [MW]'].sum() / (1000 * 4):.2f} GWh")
print(f"Gesamtbedarf 2023: {bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'].sum() / (1000 * 4):.2f} GWh")

print('Ende x_Bedarfe_gesamt.py')