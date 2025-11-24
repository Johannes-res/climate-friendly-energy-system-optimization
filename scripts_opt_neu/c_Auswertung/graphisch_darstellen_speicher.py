import pandas as pd
import matplotlib.pyplot as plt
import locale
import matplotlib.dates as mdates


#Hier darzustellenden DataFrame importieren
from vorbereitung import bedarf_deckung as df

#Hier noch Namen eintragen um Grafiken zu benennen
df_name = 'bedarf_und_deckung_speicher'  # Name des DataFrames für die Dateinamen der Grafiken


cd_palette = [
     # (0/255, 20/255, 80/255),
    (0/255, 0/255, 140/255),
    (47/255, 87/255, 178/255),
    (115/255, 105/255, 190/255),
    (188/255, 21/255, 137/255),
    (210/255, 15/255, 65/255),
    (200/255, 80/255, 0/255),
    (255/255, 199/255, 0/255),
    (118/255, 122/255, 35/255),
    (0/255, 125/255, 75/255),
    (10/255, 119/255, 127/255),
    (151/255, 198/255, 255/255),
    (200/255, 200/255, 255/255),
    (255/255, 185/255, 255/255),
    (255/255, 170/255, 165/255),
    (255/255, 190/255, 120/255),
    (255/255, 228/255, 131/255),
    (210/255, 220/255, 70/255),
    (140/255, 230/255, 170/255),
    (140/255, 230/255, 215/255)
]


#%% Graphische Darstellung für den Jahresgang

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
    try:
        locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    except locale.Error:
        print("Warnung: Das angegebene Locale 'de_DE.UTF-8' ist nicht verfügbar. Es wird das Standard-Locale verwendet.")
    fig, ax = plt.subplots(figsize=(15, 8))

    lines = []
    for idx, column in enumerate(columns):
        # Tägliche Aggregation
        df_daily = df[column].resample('D').agg(['mean', 'min', 'max'])

        # Diagramm erstellen
        # Ensure data is numeric and drop NaN values
        df_daily_clean = df_daily.dropna().apply(pd.to_numeric, errors='coerce')
        color = cd_palette[idx % len(cd_palette)]
        ax.fill_between(df_daily_clean.index, df_daily_clean['min'], df_daily_clean['max'], alpha=0.3, color=color)
        line, = ax.plot(df_daily.index, df_daily['mean'], label=column, color=color, linewidth=2)
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


#%% Graphische Darstellung für ausgewählte Tage
def plot_selected_days(df, columns, days, highlight_time=None, title=None, ylabel=None, legend_labels=None):
    """
    Erstellt ein Diagramm für ausgewählte Tage und mehrere Spalten, mit Option zum Hervorheben eines spezifischen Zeitpunkts.
    Farben werden aus cd_palette entnommen (je Spalte konsistent).
    """
    try:
        locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    except locale.Error:
        pass

    fig, ax = plt.subplots(figsize=(15, 8))

    # Farben für jede Spalte festlegen (konsistent über Tage)
    colors = {col: cd_palette[i % len(cd_palette)] for i, col in enumerate(columns)}

    seen = set()  # Damit jede Spalte nur einmal in der Legende auftaucht

    for day in days:
        # Konvertiere String zu Datum, falls nötig
        if isinstance(day, str):
            day = pd.to_datetime(day).date()

        # Filtere Daten für den ausgewählten Tag
        day_data = df[df.index.date == day]

        if day_data.empty:
            print(f"Warnung: Keine Daten für {day} gefunden.")
            continue

        # Plotte die Daten für diesen Tag und jede Spalte
        for column in columns:
            # Stelle sicher, dass Werte numerisch sind und NaNs entfernt werden
            series = pd.to_numeric(day_data[column], errors='coerce').dropna()
            if series.empty:
                print(f"Warnung: Keine gültigen Daten für Spalte '{column}' am {day}.")
                continue

            # Konvertiere Zeitindex zu Stunden seit Mitternacht (nur für die vorhandenen Indizes)
            hours_series = [
                (t - t.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 3600
                for t in series.index
            ]

            label = column if column not in seen else "_nolegend_"
            line, = ax.plot(hours_series, series.values, label=label, color=colors[column], linewidth=2)
            seen.add(column)

    ax.set_xlabel('Uhrzeit in h', fontsize=14)
    ax.set_ylabel(ylabel if ylabel else ', '.join(columns), fontsize=14)
    ax.set_title(title if title else f'Ausgewählte Spalten für ausgewählte Tage', fontsize=16)
    ax.grid(True, linestyle='--', alpha=0.7)

    # Formatiere x-Achse für bessere Lesbarkeit
    ax.set_xticks(range(0, 25, 1))  # Zeige Stunden von 0 bis 24 in 1-Stunden-Intervallen
    ax.set_xlim(0, 24)

    # Legende unter dem Diagramm anzeigen
    handles, labels = ax.get_legend_handles_labels()
    if legend_labels:
        ax.legend(handles[:len(legend_labels)], legend_labels, bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=len(legend_labels), fontsize=14)
    else:
        ax.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=min(3, len(handles)), fontsize=14)

    plt.tight_layout()
    return fig, ax

#%% Grafische Darstellung für eine Woche
def plot_weekly_aggregation(df, columns, week_start, title=None, ylabel=None, legend_labels=None):
    """
    Erstellt ein Diagramm mit stündlicher Aggregation für eine Woche und mehrere ausgewählte Spalten.
    
    :param df: pandas DataFrame mit Zeitreihenindex
    :param columns: Liste der Spaltennamen, die geplottet werden sollen
    :param week_start: Startdatum der Woche im Format 'YYYY-MM-DD'
    :param title: Titel des Diagramms (optional)
    :param ylabel: Beschriftung der y-Achse (optional)
    :param legend_labels: Benutzerdefinierte Labels für die Legende (optional)
    """
    try:
        locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    except locale.Error:
        pass

    fig, ax = plt.subplots(figsize=(15, 8))

    # Konvertiere das Startdatum zu einem Timestamp und berechne das Enddatum
    week_start = pd.to_datetime(week_start)
    week_end = week_start + pd.Timedelta(days=6)

    # Filtere die Daten für die Woche
    week_data = df[(df.index >= week_start) & (df.index <= week_end)]

    if week_data.empty:
        print(f"Warnung: Keine Daten für die Woche ab {week_start.strftime('%Y-%m-%d')} gefunden.")
        return None, None

    lines = []
    for idx, column in enumerate(columns):
        # Stündliche Aggregation
        df_hourly = week_data[column].resample('H').agg(['mean', 'min', 'max'])

        # Ensure data is numeric and drop NaN values
        df_hourly_clean = df_hourly.dropna().apply(pd.to_numeric, errors='coerce')
        if df_hourly_clean.empty:
            print(f"Warnung: Keine gültigen stündlichen Daten für Spalte '{column}' in der gewählten Woche.")
            continue

        # Farbe aus cd_palette verwenden
        color = cd_palette[idx % len(cd_palette)]

        ax.fill_between(df_hourly_clean.index, df_hourly_clean['min'], df_hourly_clean['max'], alpha=0.3, color=color)
        line, = ax.plot(df_hourly_clean.index, df_hourly_clean['mean'], label=column, color=color, linewidth=2)
        lines.append(line)

    ax.set_xlabel('Datum und Uhrzeit', fontsize=14)
    ax.set_ylabel(ylabel if ylabel else ', '.join(columns), fontsize=14)
    ax.set_title(title if title else f'Wöchentliche Werte ({week_start.strftime("%Y-%m-%d")} - {week_end.strftime("%Y-%m-%d")})', fontsize=16)
    ax.grid(True, linestyle='--', alpha=0.7)

    # X-Achse formatieren
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %d.%m'))
    fig.autofmt_xdate()

    # Legende mit benutzerdefinierten Labels anzeigen
    if legend_labels and lines:
        ax.legend(lines, legend_labels, bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=len(columns), fontsize=14)
    elif lines:
        ax.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=len(columns), fontsize=14)

    plt.tight_layout()
    return fig, ax
#%% Grafik generieren

# Grafik generieren für den Jahresgang
selected_columns =      ['Batterie_Leistung [MW]', 'Pumpspeicher_Leistung [MW]', 'H2_Speicher_Leistung [MW]']

custom_labels = selected_columns

title =                 'Netzlast und modellierte Erzeugung für das Jahr 2023'
ylabel =                'Leistung in MW'
highlight_date=         '2023-11-30'


fig, ax = plot_daily_aggregation(df, selected_columns, 
                                 highlight_date,
                                 title, 
                                 ylabel,
                                 legend_labels=custom_labels)

# Speichern der Figur
plt.savefig(f'data/c_Auswertung/{df_name}_{title}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben








# Beispielaufruf für die Darstellung eines spezifischen Tages
selected_days =                         ['2023-11-30']
# selected_columns =                       ['EMobilität', 'Wärmepumpen']
# custom_labels =                         ['Netzlast', 'modellierter Verbrauch']
title=                                  f'Netzlast und modellierte Erzeugung für den {selected_days}'
ylabel=                                 'Leistung in MW'

fig, ax = plot_selected_days(df, selected_columns, selected_days, 
                   #highlight_time='08:45',  # Hervorheben des Werts um 08:45 Uhr
                   title, 
                   ylabel,
                   legend_labels=custom_labels)

plt.savefig(f'data/c_Auswertung/{df_name}_{selected_days}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

# Beispielaufruf für die Darstellung einer Woche
week_start =                            '2023-11-27'  # Startdatum der Woche
# selected_columns =                       ['EMobilität', 'Wärmepumpen']
# custom_labels =                         ['Netzlast', 'Modellierung']
title =                                 f'Netzlast und modellierter Verbrauch für die Woche ab {week_start}'
ylabel =                                'Leistung in MW'

fig, ax = plot_weekly_aggregation(df, selected_columns, week_start,
                                  title, 
                                  ylabel,
                                  legend_labels=custom_labels)

plt.savefig(f'data/c_Auswertung/{df_name}_{week_start}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

print("Grafiken wurden erfolgreich erstellt und gespeichert.")