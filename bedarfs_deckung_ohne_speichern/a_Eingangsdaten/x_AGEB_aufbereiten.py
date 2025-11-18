import pandas as pd
import os
import numpy as np


#%% Basisjahr festlegen und AGEB-Bilanz laden
# Basisjahr festlegen
Basisjahr = 2023

# Verzeichnis, in dem die Dateien liegen
verzeichnis = r'.\data\a_Eingangsdaten\Bedarf'

# Dateiname nach Schema "EBDXXe.xlsx" erstellen
# -> letzte zwei Ziffern des Jahres extrahieren
jahr_suffix = str(Basisjahr)[-2:]
dateiname = f"EBD{jahr_suffix}e.xlsx"

# Vollständigen Pfad zusammensetzen
dateipfad = os.path.join(verzeichnis, dateiname)

# Prüfen, ob Datei existiert
if os.path.exists(dateipfad):
    df_AGEB = pd.read_excel(dateipfad)
    print(f"Tabelle aus {dateiname} geladen:")
    print(df_AGEB.head())  # Erste Zeilen anzeigen
else:
    print(f"Datei {dateiname} nicht gefunden im Verzeichnis {verzeichnis}.")

#%% Tabellenstruktur anpassen
# Umbenennen der Spaltennamen 
def rename_columns(df, column_mapping):
    """
    Benennt die Spalten eines DataFrames um.

    :param df: Der DataFrame, dessen Spalten umbenannt werden sollen.
    :param column_mapping: Ein Dictionary, das die alten Spaltennamen den neuen Spaltennamen zuordnet.
    :return: Der DataFrame mit umbenannten Spalten.
    """
    df.rename(columns=column_mapping, inplace=True)
    return df

column_mapping = {
    'Steinkohlen': 'Steinkohle',
    'Unnamed: 3': 'SteinBriketts',
    'Unnamed: 4': 'SteinKoks',
    'Unnamed: 5': 'Andere Steinkohlenprodukte',
    'Braunkohlen': 'Braunkohle',
    'Unnamed: 7': 'BraunBriketts',
    'Unnamed: 8': 'Andere Braunkohlenprodukte',
    'Unnamed: 9': 'Hartbraunkohle',
    'Mineralöle': 'Erdöl (roh)',
    'Unnamed: 11': 'Ottokraftstoff',
    'Unnamed: 12': 'Rohbenzin',
    'Unnamed: 13': 'Flugturbinenenkraftstoff',
    'Unnamed: 14': 'Dieselkraftstoff',
    'Unnamed: 15': 'Heizöl leicht',
    'Unnamed: 16': 'Heizöl schwer',
    'Unnamed: 17': 'Petrolkoks',
    'Unnamed: 18': 'Flüssigas',
    'Unnamed: 19': 'Raffeneriegas',
    'Unnamed: 20': 'Andere Mineralölprodukte',
    'Gase': 'Kokereigas, Stadtgas',
    'Unnamed: 22': 'Gichtgas, Konvertergas',
    'Unnamed: 23': 'Naturgase, Erdgas, Erdölgas',
    'Unnamed: 24': 'Grubengas',
    'Erneuerbare Energien': 'Wasserkraft, Windenergie, Photovoltaik',
    'Unnamed: 26': 'Biomasse, erneuerbare Abfälle',
    'Unnamed: 27': 'Solarthermie, Geothermie, Umweltwärme',
    'Elektrischer Strom und sonstige Energieträger': 'Fossile Abfälle, Sonstige',
    'Unnamed: 29': 'Strom',
    'Unnamed: 30': 'Kernenergie',
    'Unnamed: 31': 'Fernwärme',
    'Energieträger insgesamt': 'Primärenergieträger',
    'Unnamed: 33': 'Sekundärenergieträger',
    'Unnamed: 34': 'Summe',
}

df_AGEB = rename_columns(df_AGEB, column_mapping)


#%% Daten filtern und umstrukturieren
# Werte ab Zeile 7 und Spalte 3 zu Integers umwandeln. Die ersten 6 Zeilen und die ersten 2 Spalten sind keine Zahlen.
df_AGEB.iloc[6:, 2:] = df_AGEB.iloc[6:, 2:].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
#gesamte Werte von TJ auf GWh umrechnen
df_AGEB.iloc[6:, 2:] = df_AGEB.iloc[6:, 2:] / 3.6
# Zeile 3 ab Spalte 3 von TJoule auf GWh umbennen
df_AGEB.iloc[1, 2:] = df_AGEB.iloc[1, 2:].apply(lambda x: str(x).replace('TJ', 'GWh'))
df_AGEB.iloc[2,0] = df_AGEB.iloc[2, 0].replace('TJoule', 'GWh') #trifft noch nicht, aber egal erstmal


#df_AGEB als Excel speichern
output_path = r'.\data\a_Eingangsdaten\Bedarf\AGEB_Basisjahr_2023.xlsx'
df_AGEB.to_excel(output_path, index=False)
#Folgend kann die shifting funktion aus klimaneutral_heute.py kopiert werden und ggf. um die Untersektoren erweitert werden.

#es wird zwischen Strom alt und Strom 'neues Lastprofil' unterschieden. Ebenso bei Wasserstoff bzw. weiteren Energieträgern. Damit kann dann der Neuverbrauch für Strom alt einfach der Last hinzugefügt werden. Für Strom 'neues Lastprofil' muss dann ein neues Lastprofil erstellt werden.




#Danach muss die Verteilung auf das Jahr in einem speraten Skript erfolgen.
print("Skript ausgeführt.")