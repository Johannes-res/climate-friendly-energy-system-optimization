import requests
import pandas as pd
import holidays
import numpy as np
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates as mdates
import locale


# URL der XML-Datei
#bei 'Start' kann das Startdatum angegeben werden, bei 'End' das Enddatum
#hier wird das Startdatum auf den 01.10.2022 und das Enddatum auf den 31.10.2022 gesetzt
url = "https://datenservice.tradinghub.eu/XmlInterface/getXML.ashx?ReportId=AggregatedConsumptionData&Start=01-01-2022&End=31-12-2022"

"""https://www.tradinghub.eu/Portals/0/The_XML_Interface_V2.0_de.pdf?ver=A5R82BaYi7YlQDZEGs3inQ%3d%3d beinhaltet die Anleitung zur Nutzung der XML-Schnittstelle

Hier können die Daten der Veröffentlichung der aggregierten Verbrauchsmengen
im Marktgebiet je Gastag abgerufen werden.
Hinweis: Sollte das Startdatum nicht mit angegeben werden, wird das Startdatum
auf das Datum des ältesten Datensatzes gesetzt. Sollte das Enddatum nicht mit
angegeben werden, werden alle vorhandenen Daten, abhängig vom Startdatum
ausgegeben. Sollte kein Datum angegeben werden, werden alle Daten abgerufen.
"""



# XML-Daten abrufen
response = requests.get(url)

# XML in DataFrame umwandeln
df = pd.read_xml(response.content, xpath="//ns:AggregatedConsumptionData", namespaces={"ns": "urn:schemas-microsoft-com:sql:SqlRowSet1"})

# df.set_index('Gasday', inplace=True)
# df.index = pd.to_datetime(df.index)
df = df.drop(columns=['Unit', 'Status'])


df['Summe [MWh]'] = (df['HGasSLPsyn']+df['HGasSLPana']+df['LGasSLPsyn']+df['LGasSLPana']+df['HGasRLMmT']+df['LGasRLMmT']+df['HGasRLMoT']+df['LGasRLMoT'])/1000  # Umrechnung in MWh

df.to_excel(r'data\Ausgabe\AggregatedConsumptionData_GAS.xlsx', index=False)

df.set_index('Gasday', inplace=True)
df.index = pd.to_datetime(df.index)

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
selected_columns = ['Summe [MWh]']
custom_labels = ['Summe der verschiedenen Gassorten']
fig, ax = plot_daily_aggregation(df, selected_columns, 
                    #    highlight_date='2022-07-03',
                       title='täglicher Gasverbrauch in Deutschland 2022', 
                       ylabel='Energie in MWh',
                       legend_labels=custom_labels)

# Speichern der Figur
plt.savefig(r'graphics\GAS_22.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

# DataFrame anzeigen
# print(df)