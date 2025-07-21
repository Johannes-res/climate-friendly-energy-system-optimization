import pandas as pd
import holidays
import numpy as np
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import locale


#%% Daten laden
#lädt die Zeitreihen der Nettostromerzeugung in Deutschland für das Jahr 2022
df_energy_charts = pd.read_excel(r'data\energy-charts\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2022.xlsx')

#lädt die Endenergiebedarfsdaten für das Jahr 2022
df_AGEB = pd.read_excel(r'data\Endenergiebedarf_AGEB\EBD22e.xlsx')

#lädt die Lastprofile Haushalte H25 und Gewerbe G25
df_Lastprofil_H25 = pd.read_excel(r'data\Kopie_von_Repräsentative_Profile_BDEW_H25_G25_L25_P25_S25_Veröffentlichung.xlsx', sheet_name="H25")
df_Lastprofil_G25 = pd.read_excel(r'data\Kopie_von_Repräsentative_Profile_BDEW_H25_G25_L25_P25_S25_Veröffentlichung.xlsx', sheet_name="G25")

#lädt die aggregierten 


#%% Zeitreihe aufbereiten
#Datum als Index setzen und in Datetime umwandeln sowie erste Zeile löschen

df_energy_charts.set_index('Datum (UTC)', inplace=True)
df_energy_charts.index = pd.to_datetime(df_energy_charts.index)
df_energy_charts = df_energy_charts.drop(df_energy_charts.index[0])


# Wählen Sie das gewünschte Jahr aus (z.B. 2022)
year = 2022

# Erstellen Sie Start- und Enddatum für das ausgewählte Jahr
start_date = f"{year}-01-01 00:00:00"
end_date = f"{year}-12-31 23:45:00"

# Wählen Sie die Daten für das spezifische Jahr aus
df_selected = df_energy_charts.loc[start_date:end_date]

df_Nettostromerzeugung_22 = df_selected

#%% Lastprofile aufbereiten
def prepare_lastprofile(df):
    """
    Bereitet einen DataFrame mit Lastprofilen vor:
    - Entfernt die erste Zeile.
    - Kürzt die Zeitspalte auf die ersten 5 Zeichen, wandelt sie in datetime um und setzt sie als Index.
    - Entfernt unnötige Spalten.
    - Extrahiert Monatszahlen aus einer Zeile und setzt sie als Spaltenüberschriften.
    - Kombiniert die ersten zwei Zeilen zu neuen Spaltenüberschriften.
    - Entfernt die ersten zwei Zeilen aus dem DataFrame.

    Parameter:
        df (pd.DataFrame): Der zu bearbeitende DataFrame.

    Rückgabe:
        pd.DataFrame: Der aufbereitete DataFrame.
    """
    # Entferne die erste Zeile
    df.drop(index=0, inplace=True)

    # Extrahiere Monatszahlen aus der ersten Zeile
    df.iloc[0] = pd.to_datetime(df.iloc[0]).dt.strftime('%m')  # Konvertiere in Monatszahlen
    
    # Kombiniere die ersten zwei Zeilen zu neuen Spaltenüberschriften
    new_columns = df.iloc[:2].apply(lambda x: '_'.join(x.dropna().astype(str)), axis=0)
    
    # Setze die neuen Spaltenüberschriften
    df.columns = new_columns
    
    # Entferne die ersten zwei Zeilen aus dem DataFrame
    df = df.iloc[2:].reset_index(drop=True)

    # Kürze die Zeitspalte auf die ersten 5 Zeichen, wandle sie in datetime um und setze sie als Index
    df.iloc[:, 1] = df.iloc[:, 1].astype(str)  # Ensure the column contains strings
    df.index = pd.to_datetime(df.iloc[:, 1].str[:5], format='%H:%M').dt.time
    df.drop(df.columns[1], axis=1, inplace=True)  # Entferne die ursprüngliche Zeitspalte
    df.drop(df.columns[0], axis=1, inplace=True)
    
    return df

df_Lastprofil_G25 = prepare_lastprofile(df_Lastprofil_G25)
df_Lastprofil_H25 = prepare_lastprofile(df_Lastprofil_H25)

#%%Endenergiebedarfe für die einzelnen Sektoren aus df extrahieren
df_AGEB.set_index(df_AGEB.columns[0], inplace=True)

# Funktion, die mehrere Werte aus einem DataFrame holt
def get_values_from_dataframe(df, queries):
    """
    Holt mehrere Werte aus einem DataFrame basierend auf einer Liste von Abfragen.

    :param df: Der DataFrame, aus dem die Werte geholt werden sollen.
    :param queries: Eine Liste von Tupeln (row_name, column_name), die die gewünschten Einträge spezifizieren.
    :return: Ein DataFrame mit den Ergebnissen.
    """
    results = []
    for row_name, column_name in queries:
        try:
            value = df.loc[row_name, column_name]
            results.append({'Row': row_name, 'Column': column_name, 'Value': value})
        except KeyError:
            results.append({'Row': row_name, 'Column': column_name, 'Value': 'Fehler: Nicht gefunden'})
    return pd.DataFrame(results)

# In die Liste queries sind die gewünschten Sektoren einzutragen. 'Unnamed: 34' ist der Index der Spalte, die die Endenergiebedarfe enthält
queries = [
    ('ENDENERGIEVERBRAUCH', 'Unnamed: 34'),
    ('Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe', 'Unnamed: 34'),
    ('Verkehr insgesamt', 'Unnamed: 34'),
    ('Haushalte','Unnamed: 34'),
    ('Gewerbe, Handel, Dienstleistungen','Unnamed: 34'),
   
]

df_answer = get_values_from_dataframe(df_AGEB, queries)


df_EEB_Sektoren=pd.DataFrame()
df_EEB_Sektoren['Summe'] = df_answer.set_index('Row')['Value']  # Setzt 'Row' als Index und übernimmt die Werte aus 'Value'


# In die Liste queries sind die gewünschten Sektoren einzutragen. 'Unnamed: 29' ist der Index der Spalte, die die Strombedarfe enthält
queries = [
    ('ENDENERGIEVERBRAUCH', 'Unnamed: 29'),
    ('Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe', 'Unnamed: 29'),
    ('Verkehr insgesamt', 'Unnamed: 29'),
    ('Haushalte','Unnamed: 29'),
    ('Gewerbe, Handel, Dienstleistungen','Unnamed: 29'),
   
]

df_answer = get_values_from_dataframe(df_AGEB, queries)
df_EEB_Sektoren['Strom'] = df_answer.set_index('Row')['Value']  # Ergänzt die Werte aus 'Value' passend zum Index


#Anteile der einzelnen Sektoren am Gesamtverbrauch berechnen

df_EEB_Sektoren.loc[:,'Anteil_Summe'] = df_EEB_Sektoren.loc[:,'Summe'] / df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH', 'Summe']
df_EEB_Sektoren.loc[:,'Anteil_Strom']=df_EEB_Sektoren.loc[:,'Strom']/df_EEB_Sektoren.loc['ENDENERGIEVERBRAUCH','Strom']


#Hier wird die Gesamtenergie für das Jahr berechnet

df_Last_22 = pd.DataFrame()
df_Last_22 ['Last [MW]']=df_Nettostromerzeugung_22['Last']

df_Last_22 = df_Last_22.astype(float)  # Konvertiert die Werte in float, falls sie als Strings gespeichert sind
df_Last_22 = df_Last_22.dropna()  # Entfernt NaN-Werte

df_Last_22['Energie [MWh]'] = df_Last_22['Last [MW]']/4

var_Summe_Last_22 = df_Last_22['Energie [MWh]'].sum()  # Berechnet die Summe der Energie

var_Summe_Last_22_TWh = var_Summe_Last_22 / 1000000  # Umwandlung in TWh
var_Summe_Last_22_TWh = round(var_Summe_Last_22_TWh, 2)  # Rundet auf 2 Dezimalstellen



#Hier wird die Gesamtenergie auf die Sektoren aufgeteilt

df_EEB_Sektoren ['Stromenergiemenge_anteilig [MWh]'] = df_EEB_Sektoren['Anteil_Strom']*var_Summe_Last_22

print('Die Stromenergiemenge für 2022 beträgt:', var_Summe_Last_22_TWh, 'TWh')



#%% Funktion, welche einem Dataframe mit datetime-Index Tagesnamen (Werktag/Feiertag/Samstag) hinzufügt und den Monat angibt

def add_day_type(df):
    """
    Fügt dem DataFrame eine Spalte hinzu, die den Typ des Tages angibt (Werktag/Sonntag/Samstag) und identifiziert, ob es sich um Sommer/Winter/Übergangszeit handelt.
    :param df: DataFrame mit einem Datetime-Index."""

    # Erstelle eine Kopie des DataFrames, um die Originaldaten nicht zu verändern
    df_copy = df.copy()

    # Feiertage für Deutschland laden
    german_holidays = holidays.Germany()

    # Füge eine neue Spalte 'day_type' hinzu und initialisiere sie mit 'Werktag'
    df_copy['Tagestyp'] = 'WT'  # Standardmäßig Werktag

    # Setze den Typ des Tages auf 'Sonntag' oder 'Samstag' basierend auf dem Wochentag
    df_copy.loc[df_copy.index.weekday == 6, 'Tagestyp'] = 'FT'  # Sonntag
    df_copy.loc[df_copy.index.weekday == 5, 'Tagestyp'] = 'SA'  # Samstag

    # # Setze den Typ des Tages auf 'Feiertag' oder 'Werktag', falls noch nicht gesetzt
    # df_copy['Tagestyp'] = df_copy['Tagestyp'].fillna(
    #     df_copy.index.map(lambda date: "Feiertag" if date in german_holidays else "Werktag")
    # )


    # Füge eine neue Spalte 'Monat' hinzu, die den Monat des Datetime-Index enthält
    df_copy['Monat'] = df_copy.index.month
    df_copy['Monat'] = df_copy['Monat'].astype(str)  # Konvertiere den Monatswert in einen String
    df_copy['Monat'] = df_copy['Monat'].str.zfill(2)  # Stelle sicher, dass der Monatswert immer 2-stellig ist

    # Füge eine neue Spalte 'Monats_Tageskennung' hinzu, die die Spalte 'Tagestyp ' und 'Monat' kombiniert
    df_copy['Monats_Tageskennung'] = df_copy['Monat'].astype(str) + '_' + df_copy['Tagestyp'].astype(str)

    


   

    return df_copy

df_Last_22 = add_day_type(df_Last_22)








#%% dem Lastgang die Sektorspezifischen Lastprofile hinzufügen

def ergänze_lastprofile(df_last, df_g25, df_h25):
    """
    Ergänzt den DataFrame df_last mit den Spalten G25 und H25, basierend auf den Werten
    aus df_g25 und df_h25 entsprechend der Spalte Monats_Tageskennung und den Uhrzeiten.

    :param df_last: Der DataFrame, der ergänzt werden soll (z. B. df_Last_22).
    :param df_g25: Der DataFrame mit den Lastprofilwerten für G25.
    :param df_h25: Der DataFrame mit den Lastprofilwerten für H25.
    :return: Der ergänzte DataFrame.
    """
    # Stelle sicher, dass die Indizes von df_g25 und df_h25 datetime.time-Objekte sind
    df_g25.index = pd.to_datetime(df_g25.index, format='%H:%M:%S').time
    df_h25.index = pd.to_datetime(df_h25.index, format='%H:%M:%S').time

    # Initialisiere die neuen Spalten G25 und H25
    df_last['G25'] = df_last.apply(
        lambda row: df_g25.loc[row.name.time(), row['Monats_Tageskennung']], axis=1
    )
    df_last['H25'] = df_last.apply(
        lambda row: df_h25.loc[row.name.time(), row['Monats_Tageskennung']], axis=1
    )

    return df_last

df_Last_22_mit_Profilen = ergänze_lastprofile(df_Last_22, df_Lastprofil_G25, df_Lastprofil_H25)


#%% Sektorenzeitreihen modellieren
def saisonschwankungen_modellieren(t):
    """
    Simuliert saisonale Schwankungen im Stromverbrauch (x = Tag 1-365)
    Gibt relativen Verbrauchsfaktor zurück (1.0 = Durchschnitt)
    """
    # Jahreszeitliche Grundschwingung (Hauptmaximum im Winter)
    saison = 0.01 * np.cos(2*np.pi*(t - 15)/365)
    
    # Weihnachtseffekt (Spitze im Dezember)
    weihnachten = 0.1 * np.exp(-((t - 355)/10)**2)
    
    # Sommerdip mit leichtem Anstieg durch Kühlung
    sommer = -0.015 * np.exp(-((t - 200)/60)**2)
    
    # Zufällige tägliche Schwankungen (Rauschen)
    # rauschen = 0.05 * np.random.normal()
    
    return 1.0 + saison #+ weihnachten + sommer + rauschen


def modelliere_Sektorenzeitreihen(df_last, ESB_Industrie, ESB_GHD, ESB_Haushalte, ESB_Verkehr, faktor_G25, faktor_H25):
    """
    #Als Übergabe muss ein Zeitreihen-Dataframe mit den Lastprofilzeitreihen übergeben werden (stammt von df_Last_22_mit_Profilen)
    #Es müssen die Jahresstrommengen für die einzelnen Sektoren übergeben werden (stammt von df_EEB_Sektoren)
    
    
    Hier werden die Lastprofile mit den Stromverbräuchen der Sektoren multipliziert
    Die Lastprofile sind auf 1Mio. kWH normiert, weswegen durch 1000 geteilt werden muss um auf 1MWh zu kommen
    Für die Flexibilität wird die Rechnung mit dem gleichverteilenden Anteil erweitert """

    t= df_last.index.dayofyear
    #Die Lastprofile sind auf 1Mio. kWH normiert, weswegen durch 1000 geteilt werden muss um auf 1MWh zu kommen. Dann wird mit dem Endstrombedarf des Sektors multipliziert
    # Die Viertelstundenwerte sind in kWh angegeben, daher wird durch 10e3 geteilt, um auf MWh zu kommen
    #Energiemenge des Sektors=      ((((Lastprofil/1000)*Endstrombedarf_Sektor)/1000)*Wichtung_des_Profils + (ESB/len(df_last))*(1-faktor))*saisonschwankungen_modellieren(t)
    df_last['Industrie'] =          ((((df_last['G25']/1e3) * ESB_Industrie)/1e3)    * faktor_G25 + (ESB_Industrie/len(df_last)) * (1-faktor_G25)) *saisonschwankungen_modellieren(t)
    df_last['GHD'] =                ((((df_last['G25']/1e3) * ESB_GHD)/1e3)          * faktor_G25 + (ESB_GHD/len(df_last))       * (1-faktor_G25)) *saisonschwankungen_modellieren(t)
    df_last['Haushalte_stat'] =     ((((df_last['H25']/1e3) * ESB_Haushalte)/1e3)    * faktor_H25 + (ESB_Haushalte/len(df_last)) * (1-faktor_H25)) *saisonschwankungen_modellieren(t)
    # df_last['Haushalte_dyn'] =    ((df_last['H25'] / 1e3) * ESB_Haushalte) * (-3.92e-10 * t**4 + 3.2e-7 * t**3 - 7.02e-5 * t + 2.1e-3*t + 1.24)/1e3 #FEHLER!!!Exponentiell ansteigend!
    df_last['Verkehr'] =            (ESB_Verkehr / len(df_last))                                                                                    #*saisonschwankungen_modellieren(t)

    df_last['Summe_Sektoren_modelliert'] = (df_last['Industrie'] + df_last['GHD'] + df_last['Haushalte_stat']+df_last['Verkehr'])#*saisonschwankungen_modellieren(t)

    ##Hier wird der Anteil der einzelnen Sektoren, dynamisiert durch die Standardlastprofile, an der Gesamtlast für jede Viertelstunde berechnet
    df_last['Anteil_Industrie'] = df_last['Industrie'] / df_last['Summe_Sektoren_modelliert']
    df_last['Anteil_GHD'] = df_last['GHD'] / df_last['Summe_Sektoren_modelliert']
    df_last['Anteil_Haushalte_stat'] = df_last['Haushalte_stat'] / df_last['Summe_Sektoren_modelliert']
    # df_last['Anteil_Haushalte_dyn'] = df_last['Haushalte_dyn'] / df_last['Summe_Sektoren_modelliert']
    df_last['Anteil_Verkehr'] = df_last['Verkehr'] / df_last['Summe_Sektoren_modelliert']


    return df_last
#Endstrombedarfsanteile für die einzelnen Sektoren
#Hier die Werte für die Variablen definieren, die in der Funktion modelliere_Sektorenzeitreihen verwendet werden
ESB_Industrie       = df_EEB_Sektoren.loc['Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe','Stromenergiemenge_anteilig [MWh]']
ESB_GHD             = df_EEB_Sektoren.loc['Gewerbe, Handel, Dienstleistungen','Stromenergiemenge_anteilig [MWh]']
ESB_Haushalte       = df_EEB_Sektoren.loc['Haushalte','Stromenergiemenge_anteilig [MWh]']
ESB_Verkehr         = df_EEB_Sektoren.loc['Verkehr insgesamt','Stromenergiemenge_anteilig [MWh]']

#Hier kann man die Zeitreihen mit Faktoren beeinflussen

faktor_G25 = 0.7    # Mit welchem Anteil soll das G25-Profil in die Zeitreihe einfließen?
faktor_H25 = 0.65    # Mit welchem Anteil soll das H25-Profil in die Zeitreihe einfließen?



df_Sektorenzeitreihen_mod_1 = modelliere_Sektorenzeitreihen(df_Last_22_mit_Profilen, ESB_Industrie, ESB_GHD, ESB_Haushalte, ESB_Verkehr, faktor_G25, faktor_H25)

#Speichern der Zwischenergebnisse in eine Excel-Datei
df_Sektorenzeitreihen_mod_1.to_excel(r'data\Ausgabe\Netzlast und Sektoren nach Profilen_22.xlsx')



#Prognosewerte für die Sektoren


#Endstrombedarfsanteile für die einzelnen Sektoren
#Hier die Werte für die Variablen definieren, die in der Funktion modelliere_Sektorenzeitreihen verwendet werden
# ESB_Industrie       = 351.333e6                                                                   #MWh
# ESB_GHD             = 273.667e6/2
# ESB_Haushalte       = 273.667e6/2
# ESB_Verkehr         = 142.5e6
# ESB_gesamt          = 0.00000001


#df_Sektorenzeitreihen_mod_3 = modelliere_Sektorenzeitreihen(df_Last_22_mit_Profilen, 351.333e6, 273.667e6/2, 273.667e6/2, 142.5e6, faktor_G25, faktor_H25)



#%% Statistische Auswertung

def stat_auswertung(df_auswerten, spalte1, spalte2, spalte3):
    """
    Führt eine statistische Auswertung des DataFrames durch und gibt die Ergebnisse zurück.

    :param df_last: Der DataFrame, der ausgewertet werden soll.
    :return: Ein DataFrame mit den statistischen Auswertungen.
    """
    # Berechnung der statistischen Kennzahlen
    mean = df_auswerten[spalte1].mean()
    std = df_auswerten[spalte1].std()
    min_val = df_auswerten[spalte1].min()
    max_val = df_auswerten[spalte1].max()

    # Erstelle ein neues DataFrame für die Ergebnisse
    results = pd.DataFrame({
        'Mittelwert': mean,
        'Standardabweichung': std,
        'Minimum': min_val,
        'Maximum': max_val
    })

    return results

#%% Graphische Darstellung

def plot_daily_aggregation(df, columns, highlight_date=None, title=None, ylabel=None, legend_labels=None):
    """
    Erstellt ein Diagramm mit täglicher Aggregation für mehrere ausgewählte Spalten und optional einem hervorgehobenen Datum.
    
    :param df: pandas DataFrame mit Zeitreihenindex
    :param columns: Liste der Spaltennamen, die geplottet werden sollen
    :param highlight_date: Datum zum Hervorheben im Format 'YYYY-MM-DD' (optional)
    :param title: Titel des Diagramms (optional)
    :param ylabel: Beschriftung der y-Achse (optional)
    :param legend_labels: Benutzerdefinierte Labels für die Legende (optional)
    """
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    fig, ax = plt.subplots(figsize=(15, 8))

    lines = []
    for column in columns:
        # Tägliche Aggregation
        df_daily = df[column].resample('D').agg(['mean', 'min', 'max'])

        # Diagramm erstellen
        ax.fill_between(df_daily.index, df_daily['min'], df_daily['max'], alpha=0.3)
        line, = ax.plot(df_daily.index, df_daily['mean'], label=column)
        lines.append(line)

        # Hervorheben des spezifischen Datums, falls angegeben
        if highlight_date:
            highlight_date = pd.to_datetime(highlight_date)
            if highlight_date in df_daily.index:
                value_at_highlight = df_daily.loc[highlight_date, 'mean']
                # ax.scatter(highlight_date, value_at_highlight, color='red', s=100, zorder=5)
                # ax.annotate(f'{int(value_at_highlight)}', (highlight_date, value_at_highlight), 
                             # xytext=(5, 5), textcoords='offset points', color='red')

    ax.set_xlabel('Zeit in Monaten', fontsize=14)
    ax.set_ylabel(ylabel if ylabel else ', '.join(columns), fontsize=14)
    ax.set_title(title if title else f'Tägliche Werte über ein Jahr', fontsize=16)
    ax.grid(True, linestyle='--', alpha=0.7)

    # X-Achse formatieren
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    fig.autofmt_xdate()

    # Hervorgehobenes Datum auf x-Achse anzeigen
    if highlight_date:
        ax.axvline(x=highlight_date, color='red', linestyle='--', alpha=0.5)
        # ax.text(highlight_date, ax.get_ylim()[0], highlight_date.strftime('%Y-%m-%d'), 
                 # rotation=90, va='bottom', ha='right', color='red', alpha=0.7)

    # Legende mit benutzerdefinierten Labels anzeigen
    if legend_labels:
        ax.legend(lines, legend_labels, bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=len(columns), fontsize=14)
    else:
        ax.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=len(columns), fontsize=14)

    plt.tight_layout()
    return fig, ax
#%% Beispielaufruf
selected_columns = ['Energie [MWh]', 'Summe_Sektoren_modelliert']
custom_labels = ['Netz', 'Modellierung']
fig, ax = plot_daily_aggregation(df_Sektorenzeitreihen_mod_1, selected_columns, 
                    #    highlight_date='2022-07-03',
                       title='Netzlast und modellierter Verbrauch für das Jahr 2022', 
                       ylabel='Energie in MWh',
                       legend_labels=custom_labels)

#Speichern der Figur
plt.savefig(f'graphics\df_Sektorenzeitreihen_mod_1_jahr.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

# selected_columns = ['Energie [MWh]', 'Summe_Sektoren_modelliert']
# custom_labels = ['Netz', 'Modellierung']
# fig, ax = plot_daily_aggregation(df_Sektorenzeitreihen_mod_3, selected_columns, 
#                     #    highlight_date='2022-07-03',
#                        title='Netzlast und modellierter Verbrauch für das Jahr 2022', 
#                        ylabel='Energie in MWh',
#                        legend_labels=custom_labels)

# # Speichern der Figur
# plt.savefig(f'graphics\df_Sektorenzeitreihen_mod_3_jahr.png', dpi=300, bbox_inches='tight')
# plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

# plot_daily_aggregation(df_45, selected_columns, 
#                        highlight_date='2045-07-12',
#                        title='modellierte Last und umrichterbasierte Erzeugung für das Jahr 2045', 
#                        ylabel='Leistung in MW',
#                        legend_labels=custom_labels)
# plt.savefig(r'C:\Users\HansisRasanterRaser\Nextcloud2\SA\Ereignisse\Jahr_45.png', dpi=300, bbox_inches='tight')

#%%
def plot_selected_days(df, columns, days, highlight_time=None, title=None, ylabel=None, legend_labels=None):
    """
    Erstellt ein Diagramm für ausgewählte Tage und mehrere Spalten, mit Option zum Hervorheben eines spezifischen Zeitpunkts.
    
    :param df: pandas DataFrame mit Zeitreihenindex
    :param columns: Liste der Spaltennamen, die geplottet werden sollen
    :param days: Liste von Datumsobjekten oder Strings im Format 'YYYY-MM-DD'
    :param highlight_time: Zeitpunkt zum Hervorheben im Format 'HH:MM' (optional)
    :param title: Titel des Diagramms (optional)
    :param ylabel: Beschriftung der y-Achse (optional)
    :param legend_labels: Benutzerdefinierte Labels für die Legende (optional)
    """
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    fig, ax = plt.subplots(figsize=(15, 8))  # Erhöhte Höhe für Legende unten

    for day in days:
        # Konvertiere String zu Datum, falls nötig
        if isinstance(day, str):
            day = pd.to_datetime(day).date()
        
        # Filtere Daten für den ausgewählten Tag
        day_data = df[df.index.date == day]
        
        if day_data.empty:
            print(f"Warnung: Keine Daten für {day} gefunden.")
            continue
        
        # Konvertiere Zeitindex zu Stunden seit Mitternacht
        hours = [(t - t.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 3600 for t in day_data.index]
        
        # Plotte die Daten für diesen Tag und jede Spalte
        lines = []
        for column in columns:
            line, = ax.plot(hours, day_data[column].values, label=column)
            lines.append(line)

        # Hervorheben des spezifischen Zeitpunkts, falls angegeben
        if highlight_time:
            highlight_hour, highlight_minute = map(int, highlight_time.split(':'))
            highlight_time_point = highlight_hour + highlight_minute / 60
            
            # Finde den nächstgelegenen Zeitpunkt
            nearest_time = min(day_data.index, key=lambda x: abs(x.hour + x.minute/60 - highlight_time_point))
            
            for column in columns:
                value_at_highlight = day_data.loc[nearest_time, column]
                ax.scatter(highlight_time_point, value_at_highlight, color='red', s=50, zorder=5)
                ax.annotate(f'{int(value_at_highlight)}', (highlight_time_point, value_at_highlight), 
                             xytext=(5, 5), textcoords='offset points', color='red')

    ax.set_xlabel('Uhrzeit in h', fontsize=14)
    ax.set_ylabel(ylabel if ylabel else ', '.join(columns), fontsize=14)
    ax.set_title(title if title else f'Ausgewählte Spalten für ausgewählte Tage', fontsize=16)
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Formatiere x-Achse für bessere Lesbarkeit
    ax.set_xticks(range(0, 25, 1))  # Zeige Stunden von 0 bis 24 in 1-Stunden-Intervallen
    ax.set_xlim(0, 24)
    
    # Hervorgehobenen Zeitpunkt auf x-Achse anzeigen
    if highlight_time:
        ax.axvline(x=highlight_time_point, color='red', linestyle='--', alpha=0.5)
        # Füge den Zeitpunkt zur x-Achsen-Beschriftung hinzu
        current_xticks = list(ax.get_xticks())
        current_xlabels = [str(int(x)) for x in current_xticks]
        current_xticks.append(highlight_time_point)
        current_xlabels.append(highlight_time)
        ax.set_xticks(current_xticks)
        ax.set_xticklabels(current_xlabels, rotation=45, ha='right')

    # Legende unter dem Diagramm anzeigen
    if legend_labels:
       ax.legend(lines, legend_labels, bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=3, fontsize=14)
    else:
       ax.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=3, fontsize=14)
    
    plt.tight_layout()
    return fig, ax
#%%
# Beispielaufruf
selected_days = ['2022-02-03']
selected_columns = ['Energie [MWh]', 'Summe_Sektoren_modelliert']
custom_labels = ['Netzlast', 'modellierter Verbrauch']

fig, ax = plot_selected_days(df_Sektorenzeitreihen_mod_1, selected_columns, selected_days, 
                   #highlight_time='08:45',  # Hervorheben des Werts um 08:45 Uhr
                   title= f'Netzlast und modellierter Verbauch für den {selected_days}', 
                   ylabel='Energie in MWh',
                   legend_labels=custom_labels)

plt.savefig(f'graphics/df_Sektorenzeitreihen_mod_1_{selected_days}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

selected_days = ['2022-09-14']
selected_columns = ['Energie [MWh]', 'Summe_Sektoren_modelliert']
custom_labels = ['Netzlast', 'modellierter Verbrauch']

fig, ax = plot_selected_days(df_Sektorenzeitreihen_mod_1, selected_columns, selected_days, 
                   #highlight_time='08:45',  # Hervorheben des Werts um 08:45 Uhr
                   title= f'Netzlast und modellierter Verbauch für den {selected_days}', 
                   ylabel='Energie in MWh',
                   legend_labels=custom_labels)

plt.savefig(f'graphics/df_Sektorenzeitreihen_mod_1_{selected_days}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

selected_days = ['2022-07-25']
selected_columns = ['Energie [MWh]', 'Summe_Sektoren_modelliert']
custom_labels = ['Netzlast', 'modellierter Verbrauch']

fig, ax = plot_selected_days(df_Sektorenzeitreihen_mod_1, selected_columns, selected_days, 
                    #highlight_time='08:45',  # Hervorheben des Werts um 08:45 Uhr
                   title=f'Netzlast und modellierter Verbauch für den {selected_days}', 
                   ylabel='Energie in MWh',
                   legend_labels=custom_labels)

plt.savefig(f'graphics/df_Sektorenzeitreihen_mod_1_{selected_days}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

selected_days = ['2022-02-03']
selected_columns = ['Energie [MWh]', 'Summe_Sektoren_modelliert']
custom_labels = ['Netzlast', 'modellierter Verbrauch']

fig, ax = plot_selected_days(df_Sektorenzeitreihen_mod_3, selected_columns, selected_days, 
                   #highlight_time='08:45',  # Hervorheben des Werts um 08:45 Uhr
                   title= f'Netzlast und modellierter Verbauch für den {selected_days}', 
                   ylabel='Energie in MWh',
                   legend_labels=custom_labels)

plt.savefig(f'graphics/df_Sektorenzeitreihen_mod_3_{selected_days}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

selected_days = ['2022-09-14']
selected_columns = ['Energie [MWh]', 'Summe_Sektoren_modelliert']
custom_labels = ['Netzlast', 'modellierter Verbrauch']

fig, ax = plot_selected_days(df_Sektorenzeitreihen_mod_3, selected_columns, selected_days, 
                   #highlight_time='08:45',  # Hervorheben des Werts um 08:45 Uhr
                   title= f'Netzlast und modellierter Verbauch für den {selected_days}', 
                   ylabel='Energie in MWh',
                   legend_labels=custom_labels)

plt.savefig(f'graphics/df_Sektorenzeitreihen_mod_3_{selected_days}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

selected_days = ['2022-07-25']
selected_columns = ['Energie [MWh]', 'Summe_Sektoren_modelliert']
custom_labels = ['Netzlast', 'modellierter Verbrauch']

fig, ax = plot_selected_days(df_Sektorenzeitreihen_mod_3, selected_columns, selected_days, 
                    #highlight_time='08:45',  # Hervorheben des Werts um 08:45 Uhr
                   title=f'Netzlast und modellierter Verbauch für den {selected_days}', 
                   ylabel='Energie in MWh',
                   legend_labels=custom_labels)

plt.savefig(f'graphics/df_Sektorenzeitreihen_mod_3_{selected_days}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben