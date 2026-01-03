import pandas as pd
import matplotlib.pyplot as plt
import locale
import matplotlib.dates as mdates

# Schriftart auf Open Sans setzen
plt.rcParams['font.family'] = 'Open Sans'
plt.rcParams['font.sans-serif'] = ['Open Sans', 'Arial', 'DejaVu Sans']

#Hier darzustellenden DataFrame importieren
from vorbereitung import bedarf_deckung as df

#Hier noch Namen eintragen um Grafiken zu benennen
df_name = 'Grundmodell_Erzeugung_'  # Name des DataFrames für die Dateinamen der Grafiken
#df_name = 'energetische_Gebäudesanierung_'  # Name des DataFrames für die Dateinamen der Grafiken
#df_name = 'Verkehrswende_'


cd_palette = [
     # (0/255, 20/255, 80/255),
    (0/255, 0/255, 140/255),
    #(47/255, 87/255, 178/255),
    #(115/255, 105/255, 190/255),
    #188/255, 21/255, 137/255),
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

    # Trenne Gesamtbedarf von Erzeugern
    bedarf_column = 'Strom_Gesamt_Bedarf [MW]'
    bedarf_data = None
    bedarf_index = None
    
    # Bestimme welche Spalten gestapelt werden sollen
    stacked_columns = [col for col in columns if col != bedarf_column]
    
    # Vorbereiten der Daten für gestapelte Darstellung (nur Erzeuger)
    data_series = []
    for idx, column in enumerate(stacked_columns):
        # Tägliche Aggregation
        df_daily = df[column].resample('D').agg(['mean', 'min', 'max']) / 1000  # Umrechnung von MW in GW
        df_daily_clean = df_daily['mean'].fillna(0).apply(pd.to_numeric, errors='coerce')
        # Bei Speicherleistung nur positive Werte (Entladen) berücksichtigen
        if 'Speicher' in column:
            df_daily_clean = df_daily_clean.clip(lower=0)
        data_series.append(df_daily_clean)
    
    # Gestapeltes Flächendiagramm erstellen (nur Erzeuger)
    if data_series:
        # Farben für gestapelte Daten (beginne bei Index 1, da Index 0 für Bedarf reserviert ist)
        colors_list = [cd_palette[(i+1) % len(cd_palette)] for i in range(len(stacked_columns))]
        ax.stackplot(data_series[0].index, *[s.values for s in data_series], 
                    labels=stacked_columns, colors=colors_list, alpha=0.8)
    
    # Gesamtbedarf als Linie zeichnen (falls in columns enthalten)
    if bedarf_column in columns:
        df_daily_bedarf = df[bedarf_column].resample('D').agg(['mean', 'min', 'max']) / 1000
        df_daily_bedarf_clean = df_daily_bedarf['mean'].fillna(0).apply(pd.to_numeric, errors='coerce')
        ax.plot(df_daily_bedarf_clean.index, df_daily_bedarf_clean.values, 
               label=bedarf_column, color=cd_palette[0], linewidth=2.5, zorder=10)

        # Hervorheben des spezifischen Datums, falls angegeben
        if highlight_date:
            highlight_date = pd.to_datetime(highlight_date)
            if highlight_date in df_daily.index:
                value_at_highlight = df_daily.loc[highlight_date, 'mean']
                # ax.scatter(highlight_date, value_at_highlight, color='red', s=100, zorder=5)
                # ax.annotate(f'{int(value_at_highlight)}', (highlight_date, value_at_highlight), 
                             # xytext=(5, 5), textcoords='offset points', color='red')

    # Farbe für Achsen und Beschriftungen
    axis_color = (0/255, 20/255, 80/255)
    
    ax.set_xlabel('Zeit in Monaten', fontsize=14, color=axis_color)
    ax.set_ylabel(ylabel if ylabel else ', '.join(columns), fontsize=14, color=axis_color)
    ax.set_title(title if title else f'Tägliche Werte über ein Jahr', fontsize=16, color=axis_color)
    ax.tick_params(colors=axis_color)
    
    # Achsen mit Pfeilen versehen
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(axis_color)
    ax.spines['left'].set_color(axis_color)
    ax.spines['bottom'].set_linewidth(1.5)
    ax.spines['left'].set_linewidth(1.5)
    
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
    handles, labels = ax.get_legend_handles_labels()
    if legend_labels:
        # Labels müssen in der gleichen Reihenfolge wie die Handles sein:
        # Zuerst alle gestapelten Spalten, dann Bedarf
        bedarf_column = 'Strom_Gesamt_Bedarf [MW]'
        reordered_labels = []
        for col in columns:
            if col != bedarf_column:
                idx = columns.index(col)
                reordered_labels.append(legend_labels[idx])
        # Füge Bedarf-Label hinzu, falls vorhanden
        if bedarf_column in columns:
            idx = columns.index(bedarf_column)
            reordered_labels.append(legend_labels[idx])
        ax.legend(handles, reordered_labels, bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)
    else:
        ax.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)

    plt.tight_layout()
    
    # Pfeile am Ende der Achsen hinzufügen
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    arrow_length = (xlim[1] - xlim[0]) * 0.02
    arrow_height = (ylim[1] - ylim[0]) * 0.02
    
    # Pfeil am Ende der x-Achse
    ax.annotate('', xy=(xlim[1], ylim[0]), xytext=(xlim[1] - arrow_length, ylim[0]),
                arrowprops=dict(arrowstyle='->', color=axis_color, lw=1.5),
                clip_on=False)
    # Pfeil am Ende der y-Achse
    ax.annotate('', xy=(xlim[0], ylim[1]), xytext=(xlim[0], ylim[1] - arrow_height),
                arrowprops=dict(arrowstyle='->', color=axis_color, lw=1.5),
                clip_on=False)

    return fig, ax


#%% Graphische Darstellung für ausgewählte Tage
def plot_selected_days(df, columns, day, highlight_time=None, title=None, ylabel=None, legend_labels=None):
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

    # Konvertiere String zu Datum, falls nötig
    if isinstance(day, str):
        day = pd.to_datetime(day).date()

    # Filtere Daten für den ausgewählten Tag
    day_data = df[df.index.date == day]

    if day_data.empty:
        print(f"Warnung: Keine Daten für {day} gefunden.")
        return None, None

    # Trenne Gesamtbedarf von Erzeugern
    bedarf_column = 'Strom_Gesamt_Bedarf [MW]'
    stacked_columns = [col for col in columns if col != bedarf_column]

    # Vorbereiten der Daten für gestapelte Darstellung (nur Erzeuger)
    data_series = []
    hours_series = None
    for column in stacked_columns:
        # Stelle sicher, dass Werte numerisch sind und NaNs entfernt werden
        series = pd.to_numeric(day_data[column], errors='coerce').fillna(0) / 1000  # Umrechnung von MW in GW
        
        # Bei Speicherleistung nur positive Werte (Entladen) berücksichtigen
        if 'Speicher' in column:
            series = series.clip(lower=0)
        
        if hours_series is None:
            # Konvertiere Zeitindex zu Stunden seit Mitternacht
            hours_series = [
                (t - t.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 3600
                for t in series.index
            ]
        
        data_series.append(series.values)
    
    # Gestapeltes Flächendiagramm erstellen (nur Erzeuger)
    if data_series and hours_series:
        # Farben für gestapelte Daten (beginne bei Index 1, da Index 0 für Bedarf reserviert ist)
        colors_list = [colors[col] for col in stacked_columns]
        ax.stackplot(hours_series, *data_series, labels=stacked_columns, colors=colors_list, alpha=0.8)
    
    # Gesamtbedarf als Linie zeichnen (falls in columns enthalten)
    if bedarf_column in columns and hours_series:
        bedarf_series = pd.to_numeric(day_data[bedarf_column], errors='coerce').fillna(0) / 1000
        ax.plot(hours_series, bedarf_series.values, 
               label=bedarf_column, color=colors[bedarf_column], linewidth=2.5, zorder=10)

    # Farbe für Achsen und Beschriftungen
    axis_color = (0/255, 20/255, 80/255)
    
    ax.set_xlabel('Uhrzeit in h', fontsize=14, color=axis_color)
    ax.set_ylabel(ylabel if ylabel else ', '.join(columns), fontsize=14, color=axis_color)
    ax.set_title(title if title else f'Ausgewählte Spalten für ausgewählte Tage', fontsize=16, color=axis_color)
    ax.tick_params(colors=axis_color)
    
    # Achsen mit Pfeilen versehen
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(axis_color)
    ax.spines['left'].set_color(axis_color)
    ax.spines['bottom'].set_linewidth(1.5)
    ax.spines['left'].set_linewidth(1.5)
    
    ax.grid(True, linestyle='--', alpha=0.7)

    # Formatiere x-Achse für bessere Lesbarkeit
    ax.set_xticks(range(0, 25, 1))  # Zeige Stunden von 0 bis 24 in 1-Stunden-Intervallen
    ax.set_xlim(0, 24)
    
    # Legende unter dem Diagramm anzeigen
    handles, labels = ax.get_legend_handles_labels()
    if legend_labels:
        # Labels müssen in der gleichen Reihenfolge wie die Handles sein:
        # Zuerst alle gestapelten Spalten, dann Bedarf
        bedarf_column = 'Strom_Gesamt_Bedarf [MW]'
        reordered_labels = []
        for col in columns:
            if col != bedarf_column:
                idx = columns.index(col)
                reordered_labels.append(legend_labels[idx])
        # Füge Bedarf-Label hinzu, falls vorhanden
        if bedarf_column in columns:
            idx = columns.index(bedarf_column)
            reordered_labels.append(legend_labels[idx])
        ax.legend(handles, reordered_labels, bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)
    else:
        ax.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)

    plt.tight_layout()
    
    # Pfeile am Ende der Achsen hinzufügen
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    arrow_length = (xlim[1] - xlim[0]) * 0.02
    arrow_height = (ylim[1] - ylim[0]) * 0.02
    
    # Pfeil am Ende der x-Achse
    ax.annotate('', xy=(xlim[1], ylim[0]), xytext=(xlim[1] - arrow_length, ylim[0]),
                arrowprops=dict(arrowstyle='->', color=axis_color, lw=1.5),
                clip_on=False)
    # Pfeil am Ende der y-Achse
    ax.annotate('', xy=(xlim[0], ylim[1]), xytext=(xlim[0], ylim[1] - arrow_height),
                arrowprops=dict(arrowstyle='->', color=axis_color, lw=1.5),
                clip_on=False)

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

    # Trenne Gesamtbedarf von Erzeugern
    bedarf_column = 'Strom_Gesamt_Bedarf [MW]'
    stacked_columns = [col for col in columns if col != bedarf_column]

    # Vorbereiten der Daten für gestapelte Darstellung (nur Erzeuger)
    data_series = []
    for idx, column in enumerate(stacked_columns):
        # Stündliche Aggregation mit Umrechnung von MW in GW
        df_hourly = week_data[column].resample('H').agg(['mean', 'min', 'max']) / 1000
        df_hourly_clean = df_hourly['mean'].fillna(0).apply(pd.to_numeric, errors='coerce')
        # Bei Speicherleistung nur positive Werte (Entladen) berücksichtigen
        if 'Speicher' in column:
            df_hourly_clean = df_hourly_clean.clip(lower=0)
        data_series.append(df_hourly_clean)
    
    # Gestapeltes Flächendiagramm erstellen (nur Erzeuger)
    if data_series:
        # Farben für gestapelte Daten (beginne bei Index 1, da Index 0 für Bedarf reserviert ist)
        colors_list = [cd_palette[(i+1) % len(cd_palette)] for i in range(len(stacked_columns))]
        ax.stackplot(data_series[0].index, *[s.values for s in data_series], 
                    labels=stacked_columns, colors=colors_list, alpha=0.8)
    
    # Gesamtbedarf als Linie zeichnen (falls in columns enthalten)
    if bedarf_column in columns:
        df_hourly_bedarf = week_data[bedarf_column].resample('H').agg(['mean', 'min', 'max']) / 1000
        df_hourly_bedarf_clean = df_hourly_bedarf['mean'].fillna(0).apply(pd.to_numeric, errors='coerce')
        ax.plot(df_hourly_bedarf_clean.index, df_hourly_bedarf_clean.values, 
               label=bedarf_column, color=cd_palette[0], linewidth=2.5, zorder=10)

    # Farbe für Achsen und Beschriftungen
    axis_color = (0/255, 20/255, 80/255)
    
    ax.set_xlabel('Datum und Uhrzeit', fontsize=14, color=axis_color)
    ax.set_ylabel(ylabel if ylabel else ', '.join(columns), fontsize=14, color=axis_color)
    ax.set_title(title if title else f'Wöchentliche Werte ({week_start.strftime("%Y-%m-%d")} - {week_end.strftime("%Y-%m-%d")})', fontsize=16, color=axis_color)
    ax.tick_params(colors=axis_color)
    
    # Achsen mit Pfeilen versehen
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(axis_color)
    ax.spines['left'].set_color(axis_color)
    ax.spines['bottom'].set_linewidth(1.5)
    ax.spines['left'].set_linewidth(1.5)
    
    ax.grid(True, linestyle='--', alpha=0.7)

    # X-Achse formatieren
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %d.%m'))
    fig.autofmt_xdate()
    
    # Legende mit benutzerdefinierten Labels anzeigen
    handles, labels = ax.get_legend_handles_labels()
    if legend_labels and handles:
        # Labels müssen in der gleichen Reihenfolge wie die Handles sein:
        # Zuerst alle gestapelten Spalten, dann Bedarf
        bedarf_column = 'Strom_Gesamt_Bedarf [MW]'
        reordered_labels = []
        for col in columns:
            if col != bedarf_column:
                idx = columns.index(col)
                reordered_labels.append(legend_labels[idx])
        # Füge Bedarf-Label hinzu, falls vorhanden
        if bedarf_column in columns:
            idx = columns.index(bedarf_column)
            reordered_labels.append(legend_labels[idx])
        ax.legend(handles, reordered_labels, bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)
    elif handles:
        ax.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)

    plt.tight_layout()
    
    # Pfeile am Ende der Achsen hinzufügen
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    arrow_length = (xlim[1] - xlim[0]) * 0.02
    arrow_height = (ylim[1] - ylim[0]) * 0.02
    
    # Pfeil am Ende der x-Achse
    ax.annotate('', xy=(xlim[1], ylim[0]), xytext=(xlim[1] - arrow_length, ylim[0]),
                arrowprops=dict(arrowstyle='->', color=axis_color, lw=1.5),
                clip_on=False)
    # Pfeil am Ende der y-Achse
    ax.annotate('', xy=(xlim[0], ylim[1]), xytext=(xlim[0], ylim[1] - arrow_height),
                arrowprops=dict(arrowstyle='->', color=axis_color, lw=1.5),
                clip_on=False)

    return fig, ax

#%% Grafische Darstellung für einen Monat
def plot_monthly_aggregation(df, columns, month_start, title=None, ylabel=None, legend_labels=None):
    """
    Erstellt ein Diagramm mit stündlicher Aggregation für einen Monat und mehrere ausgewählte Spalten.
    
    :param df: pandas DataFrame mit Zeitreihenindex
    :param columns: Liste der Spaltennamen, die geplottet werden sollen
    :param month_start: Startdatum des Monats im Format 'YYYY-MM-DD' oder 'YYYY-MM'
    :param title: Titel des Diagramms (optional)
    :param ylabel: Beschriftung der y-Achse (optional)
    :param legend_labels: Benutzerdefinierte Labels für die Legende (optional)
    """
    try:
        locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    except locale.Error:
        pass

    fig, ax = plt.subplots(figsize=(15, 8))

    # Konvertiere das Startdatum zu einem Timestamp
    month_start = pd.to_datetime(month_start)
    
    # Berechne das Enddatum (letzter Tag des Monats)
    if month_start.month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - pd.Timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1, day=1) - pd.Timedelta(days=1)
    
    # Setze die Zeit auf das Ende des letzten Tages
    month_end = month_end.replace(hour=23, minute=59, second=59)

    # Filtere die Daten für den Monat
    month_data = df[(df.index >= month_start) & (df.index <= month_end)]

    if month_data.empty:
        print(f"Warnung: Keine Daten für den Monat ab {month_start.strftime('%Y-%m-%d')} gefunden.")
        return None, None

    # Trenne Gesamtbedarf von Erzeugern
    bedarf_column = 'Strom_Gesamt_Bedarf [MW]'
    stacked_columns = [col for col in columns if col != bedarf_column]

    # Vorbereiten der Daten für gestapelte Darstellung (nur Erzeuger)
    data_series = []
    for idx, column in enumerate(stacked_columns):
        # Stündliche Aggregation mit Umrechnung von MW in GW
        df_hourly = month_data[column].resample('H').agg(['mean', 'min', 'max']) / 1000
        df_hourly_clean = df_hourly['mean'].fillna(0).apply(pd.to_numeric, errors='coerce')
        # Bei Speicherleistung nur positive Werte (Entladen) berücksichtigen
        if 'Speicher' in column:
            df_hourly_clean = df_hourly_clean.clip(lower=0)
        data_series.append(df_hourly_clean)
    
    # Gestapeltes Flächendiagramm erstellen (nur Erzeuger)
    if data_series:
        # Farben für gestapelte Daten (beginne bei Index 1, da Index 0 für Bedarf reserviert ist)
        colors_list = [cd_palette[(i+1) % len(cd_palette)] for i in range(len(stacked_columns))]
        ax.stackplot(data_series[0].index, *[s.values for s in data_series], 
                    labels=stacked_columns, colors=colors_list, alpha=0.8)
    
    # Gesamtbedarf als Linie zeichnen (falls in columns enthalten)
    if bedarf_column in columns:
        df_hourly_bedarf = month_data[bedarf_column].resample('H').agg(['mean', 'min', 'max']) / 1000
        df_hourly_bedarf_clean = df_hourly_bedarf['mean'].fillna(0).apply(pd.to_numeric, errors='coerce')
        ax.plot(df_hourly_bedarf_clean.index, df_hourly_bedarf_clean.values, 
               label=bedarf_column, color=cd_palette[0], linewidth=2.5, zorder=10)

    # Farbe für Achsen und Beschriftungen
    axis_color = (0/255, 20/255, 80/255)
    
    ax.set_xlabel('Datum und Uhrzeit', fontsize=14, color=axis_color)
    ax.set_ylabel(ylabel if ylabel else ', '.join(columns), fontsize=14, color=axis_color)
    ax.set_title(title if title else f'Monatliche Werte ({month_start.strftime("%B %Y")})', fontsize=16, color=axis_color)
    ax.tick_params(colors=axis_color)
    
    # Achsen mit Pfeilen versehen
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(axis_color)
    ax.spines['left'].set_color(axis_color)
    ax.spines['bottom'].set_linewidth(1.5)
    ax.spines['left'].set_linewidth(1.5)
    
    ax.grid(True, linestyle='--', alpha=0.7)

    # X-Achse formatieren
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    ax.xaxis.set_minor_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    fig.autofmt_xdate()
    
    # Legende mit benutzerdefinierten Labels anzeigen
    handles, labels = ax.get_legend_handles_labels()
    if legend_labels and handles:
        # Labels müssen in der gleichen Reihenfolge wie die Handles sein:
        # Zuerst alle gestapelten Spalten, dann Bedarf
        bedarf_column = 'Strom_Gesamt_Bedarf [MW]'
        reordered_labels = []
        for col in columns:
            if col != bedarf_column:
                idx = columns.index(col)
                reordered_labels.append(legend_labels[idx])
        # Füge Bedarf-Label hinzu, falls vorhanden
        if bedarf_column in columns:
            idx = columns.index(bedarf_column)
            reordered_labels.append(legend_labels[idx])
        ax.legend(handles, reordered_labels, bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)
    elif handles:
        ax.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)

    plt.tight_layout()
    
    # Pfeile am Ende der Achsen hinzufügen
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    arrow_length = (xlim[1] - xlim[0]) * 0.02
    arrow_height = (ylim[1] - ylim[0]) * 0.02
    
    # Pfeil am Ende der x-Achse
    ax.annotate('', xy=(xlim[1], ylim[0]), xytext=(xlim[1] - arrow_length, ylim[0]),
                arrowprops=dict(arrowstyle='->', color=axis_color, lw=1.5),
                clip_on=False)
    # Pfeil am Ende der y-Achse
    ax.annotate('', xy=(xlim[0], ylim[1]), xytext=(xlim[0], ylim[1] - arrow_height),
                arrowprops=dict(arrowstyle='->', color=axis_color, lw=1.5),
                clip_on=False)

    return fig, ax

#%% Grafik generieren

# Grafik generieren für den Jahresgang
selected_columns =      ['Strom_Gesamt_Bedarf [MW]', 'Fotovoltaik', 'Wind_Onshore', 'Wind_Offshore', 'Laufwasser','Summe_Speicher_Leistung [MW]' ]

custom_labels = ['Gesamtbedarf', 'Fotovoltaik', 'Wind Onshore', 'Wind Offshore', 'Laufwasser','Summe der Entladeleistung der Speicher' ]
title =                 'optimierte Bedarfsdeckung im Jahresverlauf'
ylabel =                'Leistung in GW'
highlight_date=         None


fig, ax = plot_daily_aggregation(df, selected_columns, 
                                 highlight_date,
                                 title, 
                                 ylabel,
                                 legend_labels=custom_labels)

# Speichern der Figur
plt.savefig(f'data/c_Auswertung/{df_name}_{title}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben








# Beispielaufruf für die Darstellung eines spezifischen Tages
selected_days =                         '2023-12-04'
# selected_columns =      ['Strom_Gesamt_Bedarf [MW]', 'Fotovoltaik', 'Wind_Onshore', 'Wind_Offshore', 'Laufwasser','Batterie_Leistung [MW]', 'Pumpspeicher_Leistung [MW]', 'H2_Speicher_Leistung [MW]' ]

# custom_labels = ['Gesamtbedarf', 'Fotovoltaik', 'Wind Onshore', 'Wind Offshore', 'Laufwasser','Batterie', 'Pumpspeicher', 'Wasserstoff' ]
title=                                  f'optimierte Bedarfsdeckung für den {selected_days}'
ylabel=                                 'Leistung in GW'

fig, ax = plot_selected_days(df, selected_columns, selected_days, 
                   None,  # Hervorheben des Werts um 08:45 Uhr
                   title, 
                   ylabel,
                   legend_labels=custom_labels)

plt.savefig(f'data/c_Auswertung/{df_name}_{selected_days}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

# Beispielaufruf für die Darstellung einer Woche
week_start =                            '2023-12-01'  # Startdatum der Woche
#selected_columns =                       ['EMobilität', 'Wärmepumpen']
#custom_labels =                         ['Netzlast', 'Modellierung']
title =                                 f'optimierte Bedarfsdeckung für die Woche ab {week_start}'
ylabel =                                'Leistung in GW'

fig, ax = plot_weekly_aggregation(df, selected_columns, week_start,
                                  title, 
                                  ylabel,
                                  legend_labels=custom_labels)

plt.savefig(f'data/c_Auswertung/{df_name}_{week_start}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

# Beispielaufruf für die Darstellung eines Monats
month_start =                           '2023-12-01'  # Startdatum des Monats
#selected_columns =                       ['EMobilität', 'Wärmepumpen']
#custom_labels =                         ['Netzlast', 'Modellierung']
title =                                 f'optimierte Bedarfsdeckung für den Monat {pd.to_datetime(month_start).strftime("%B %Y")}'
ylabel =                                'Leistung in GW'

fig, ax = plot_monthly_aggregation(df, selected_columns, month_start,
                                   title, 
                                   ylabel,
                                   legend_labels=custom_labels)

plt.savefig(f'data/c_Auswertung/{df_name}_{month_start}_month.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

print("Grafiken wurden erfolgreich erstellt und gespeichert.")