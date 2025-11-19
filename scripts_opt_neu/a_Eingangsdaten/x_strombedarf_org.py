import pandas as pd

strom_last_23 = pd.read_excel(r'data\a_Eingangsdaten\Strom\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2023.xlsx')

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

#Biomasse und Müll von der Last abziehen, da diese nicht erweitert werden können
strom_last_23['Last'] = strom_last_23['Last'] - strom_last_23['Biomasse'] - strom_last_23['Müll']

#Aus dem df strom_last_23 alles bis auf die Spalte 'Last' droppen
strom_last_23 = strom_last_23[['Last']]
strom_last_23.rename(columns={'Last': 'Strom_Last [MW]'}, inplace=True)

#Zu strom_last_23 noch eine Spalte mit dem gleichverteilenten Jahresstrombedarf der Industrie hinzufügen
jahresstrombedarf_industrie = 400000  # in GWh
strom_last_23['Industrie_Strom_Last [MW]'] = jahresstrombedarf_industrie * 1000 / (365 * 24)  # Umrechnung in MW und Verteilung auf 15-Minuten-Intervalle

print('Ende x_strombedarf_org.py')