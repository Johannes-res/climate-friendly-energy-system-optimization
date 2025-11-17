import pandas as pd

strom_erzeuger_23 = pd.read_excel(r'data\a_Eingangsdaten\Strom\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2023.xlsx')

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

#Aussortieren von unwichtigen Spalten (nur Erzeuger, keine Last etc.)
    df_selected = df_selected.drop(columns=['Last', 'Residuallast', 'Grenzüberschreitender Stromhandel', 'Pumpspeicher', 'Speicherwasser'])
    df_selected.rename(columns=lambda x: x.strip().replace(' ', '_'), inplace=True)  # Leerzeichen durch '_' ersetzen und führende/trailende Leerzeichen entfernen
    df_selected.rename(columns={'Solar': 'Fotovoltaik'}, inplace=True)

#Maximalwerte pro Spalte finden und Werte mit diesen normieren
    for column in df_selected.columns:
        max_value = df_selected[column].abs().max()
       
        df_selected[column] = df_selected[column] / max_value  # Normierung auf Maximalwert um so die Verfügbarkeit in [0,1] zu bekommen

    return df_selected

strom_verfügbarkeiten_23 = prepare_energy_charts(strom_erzeuger_23, 2023)

strom_verfügbarkeiten_23.to_excel(r'data\b_Optimierung\Verfügbarkeiten_Stromerzeuger_15min_2023.xlsx', index=True)


print('Ende y_verfügbarkeiten_strom.py')