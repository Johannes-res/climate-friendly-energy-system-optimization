Modellvariante = 'Basisjahr_2022_'

import pandas as pd
import os
from pathlib import Path

# Wechsle zum Projekt-Root (2 Ebenen nach oben vom Skript)
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)
print(f"Working Directory: {os.getcwd()}")

strom_last_23 = pd.read_excel(r'data\a_Eingangsdaten\Strom\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2023.xlsx')
strom_last_22 = pd.read_excel(r'data\a_Eingangsdaten\Strom\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2022.xlsx')
strom_last_24 = pd.read_excel(r'data\a_Eingangsdaten\Strom\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2024.xlsx')

#strom_last_23.index = pd.to_datetime(strom_last_23.iloc[:, 0], format='%Y-%m-%d %H:%M:%S')


#%% Zeitreihe aufbereiten


def prepare_energy_charts(df, year):

#Datum als Index setzen und in Datetime umwandeln sowie erste Zeile löschen

    df.set_index('Datum (UTC)', inplace=True)
    df.index = pd.to_datetime(df.index)
    df = df.drop(df.index[0])

# Erstellen von Start- und Enddatum für das ausgewählte Jahr
    start_date = f"{year}-01-01 00:00:00"
    end_date = f"{year}-12-31 23:45:00"

# Auswählen der Daten für das spezifische Jahr 
    df_selected = df.loc[start_date:end_date]

    return df_selected

strom_last_23 = prepare_energy_charts(strom_last_23, 2023)
strom_last_22 = prepare_energy_charts(strom_last_22, 2022)
strom_last_24 = prepare_energy_charts(strom_last_24, 2024)


print(f"Stromgesamtbedarf 2023: {strom_last_23['Last'].sum() / (1000 * 4):.2f} GWh")
print(f"Maximalwert Stromgesamtbedarf in MW: {strom_last_23['Last'].max()/1000:.2f} GW zum Zeitpunkt {strom_last_23['Last'].idxmax()}")
print(f"Minimalwert Stromgesamtbedarf in MW: {strom_last_23['Last'].min()/1000:.2f} GW zum Zeitpunkt {strom_last_23['Last'].idxmin()}")
strom_last_23_original = strom_last_23['Last'].copy()
strom_last_23_original = strom_last_23_original.to_frame()  # Convert Series to DataFrame
#Biomasse und Müll von der Last abziehen, da diese nicht erweitert werden können
strom_last_23['Last'] = strom_last_23['Last'] - strom_last_23['Biomasse'] - strom_last_23['Müll']

#Aus dem df strom_last_23 alles bis auf die Spalte 'Last' droppen
strom_last_23 = strom_last_23[['Last']]
strom_last_23.rename(columns={'Last': 'Strom_Last [MW]'}, inplace=True)

print(f"Stromgesamtbedarf 2022: {strom_last_22['Last'].sum() / (1000 * 4):.2f} GWh")
print(f"Maximalwert Stromgesamtbedarf in MW: {strom_last_22['Last'].max()/1000:.2f} GW zum Zeitpunkt {strom_last_22['Last'].idxmax()}")
print(f"Minimalwert Stromgesamtbedarf in MW: {strom_last_22['Last'].min()/1000:.2f} GW zum Zeitpunkt {strom_last_22['Last'].idxmin()}")
strom_last_22_original = strom_last_22['Last'].copy()
strom_last_22_original = strom_last_22_original.to_frame()  # Convert Series to DataFrame
#Biomasse und Müll von der Last abziehen, da diese nicht erweitert werden können
strom_last_22['Last'] = strom_last_22['Last'] - strom_last_22['Biomasse'] - strom_last_22['Müll']

#Aus dem df strom_last_22 alles bis auf die Spalte 'Last' droppen
strom_last_22 = strom_last_22[['Last']]
strom_last_22.rename(columns={'Last': 'Strom_Last [MW]'}, inplace=True)

print(f"Stromgesamtbedarf 2024: {strom_last_24['Last'].sum() / (1000 * 4):.2f} GWh")
print(f"Maximalwert Stromgesamtbedarf in MW: {strom_last_24['Last'].max()/1000:.2f} GW zum Zeitpunkt {strom_last_24['Last'].idxmax()}")
print(f"Minimalwert Stromgesamtbedarf in MW: {strom_last_24['Last'].min()/1000:.2f} GW zum Zeitpunkt {strom_last_24['Last'].idxmin()}")
strom_last_24_original = strom_last_24['Last'].copy()
strom_last_24_original = strom_last_24_original.to_frame()  # Convert Series to DataFrame
#Biomasse und Müll von der Last abziehen, da diese nicht erweitert werden können
strom_last_24['Last'] = strom_last_24['Last'] - strom_last_24['Biomasse'] - strom_last_24['Müll']

#Aus dem df strom_last_24 alles bis auf die Spalte 'Last' droppen
strom_last_24 = strom_last_24[['Last']]
strom_last_24.rename(columns={'Last': 'Strom_Last [MW]'}, inplace=True)

print('Ende x_strombedarf_org.py')