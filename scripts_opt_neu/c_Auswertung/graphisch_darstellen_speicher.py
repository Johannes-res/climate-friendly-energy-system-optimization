import pandas as pd
import matplotlib.pyplot as plt
import locale
import matplotlib.dates as mdates
import numpy as np

# Schriftart auf Open Sans setzen
plt.rcParams['font.family'] = 'Open Sans'
plt.rcParams['font.sans-serif'] = ['Open Sans', 'Arial', 'DejaVu Sans']


#Modellvariante = 'Grundmodell_'
#Modellvariante = 'energetische_Gebäudesanierung_'
Modellvariante = 'Verkehrswende_'
#Hier darzustellenden DataFrame importieren
df_batterie = pd.read_excel(f'data/b_Optimierung/{Modellvariante}opt_speicher_zeitreihen.xlsx', index_col=0, sheet_name='Batteriespeicher_Batterie')
df_pump = pd.read_excel(f'data/b_Optimierung/{Modellvariante}opt_speicher_zeitreihen.xlsx', index_col=0, sheet_name='Pumpspeicher_Pump')
df_wasserstoff = pd.read_excel(f'data/b_Optimierung/{Modellvariante}opt_speicher_zeitreihen.xlsx', index_col=0, sheet_name='Wasserstoffkaverne_H2')

df_speicher = pd.DataFrame({
    'Batterie_stand [%]': df_batterie['SOC [%]'],
    'Pumpspeicher_stand [%]': df_pump['SOC [%]'].reindex(df_batterie.index, method='ffill'),
    'H2_Speicher_stand [%]': df_wasserstoff['SOC [%]'].reindex(df_batterie.index, method='ffill')
})


df= df_speicher.copy()

#Hier noch Namen eintragen um Grafiken zu benennen
#df_name = 'Grundmodell_Speicher_'  # Name des DataFrames für die Dateinamen der Grafiken
#df_name = 'energetische_Gebäudesanierung_'  # Name des DataFrames für die Dateinamen der Grafiken
df_name = 'Verkehrswende_Speicher_'


cd_palette = [
     # (0/255, 20/255, 80/255),
    (0/255, 0/255, 140/255),
    #(47/255, 87/255, 178/255),
    #(115/255, 105/255, 190/255),
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


#%% Auswertungsfunktion

def analyze_data(df, columns, time_period='Jahr', period_data=None):
    """
    Analysiert die Daten und gibt wichtige Kennzahlen aus.
    
    :param df: pandas DataFrame mit Zeitreihenindex
    :param columns: Liste der Spaltennamen, die analysiert werden sollen
    :param time_period: Bezeichnung des Zeitraums ('Jahr', 'Tag', 'Woche', 'Monat')
    :param period_data: Optional: gefilterte Daten für den spezifischen Zeitraum
    :return: Dictionary mit Analyseergebnissen
    """
    if period_data is None:
        period_data = df
    
    analysis_results = {}
    
    print(f"\n{'='*80}")
    print(f"AUSWERTUNG: {time_period}")
    print(f"{'='*80}\n")
    
    for column in columns:
        if column not in period_data.columns:
            continue
            
        # Konvertiere zu numerischen Werten
        data = pd.to_numeric(period_data[column], errors='coerce').dropna()
        
        if len(data) == 0:
            continue
        
        # Berechne Kennzahlen in GW
        data_gw = data / 1000
        
        max_val = data_gw.max()
        min_val = data_gw.min()
        mean_val = data_gw.mean()
        median_val = data_gw.median()
        std_val = data_gw.std()
        
        # Finde Zeitpunkt des Maximums und Minimums
        max_time = data_gw.idxmax()
        min_time = data_gw.idxmin()
        
        # Speichere Ergebnisse
        analysis_results[column] = {
            'max': max_val,
            'min': min_val,
            'mean': mean_val,
            'median': median_val,
            'std': std_val,
            'max_time': max_time,
            'min_time': min_time
        }
        
        # Ausgabe
        print(f"{column}:")
        print(f"  Maximum:       {max_val:>8.2f} GW  (am {max_time.strftime('%Y-%m-%d %H:%M')})")
        print(f"  Minimum:       {min_val:>8.2f} GW  (am {min_time.strftime('%Y-%m-%d %H:%M')})")
        print(f"  Mittelwert:    {mean_val:>8.2f} GW")
        print(f"  Median:        {median_val:>8.2f} GW")
        print(f"  Std.abw.:      {std_val:>8.2f} GW")
        
        # Berechne Gesamtenergie (nur wenn Zeitdelta verfügbar)
        if len(data) > 1:
            # Annahme: Daten sind in gleichmäßigen Zeitschritten
            time_diff = (data.index[1] - data.index[0]).total_seconds() / 3600  # in Stunden
            total_energy_twh = (data_gw.sum() * time_diff) / 1000  # in TWh
            print(f"  Gesamtenergie: {total_energy_twh:>8.2f} TWh")
            analysis_results[column]['total_energy'] = total_energy_twh
        
        # Spezielle Analyse für Speicher (positive und negative Werte)
        if 'Speicher' in column or 'Batterie' in column or 'Pumpspeicher' in column:
            positive_energy = data_gw[data_gw > 0].sum() * time_diff / 1000 if len(data) > 1 else 0
            negative_energy = data_gw[data_gw < 0].sum() * time_diff / 1000 if len(data) > 1 else 0
            print(f"  Entladen:      {positive_energy:>8.2f} TWh")
            print(f"  Laden:         {negative_energy:>8.2f} TWh")
            if positive_energy != 0:
                efficiency = abs(negative_energy) / positive_energy * 100
                print(f"  Wirkungsgrad:  {efficiency:>8.2f} %")
                analysis_results[column]['efficiency'] = efficiency
            analysis_results[column]['discharge_energy'] = positive_energy
            analysis_results[column]['charge_energy'] = negative_energy
        
        print()
    
    print(f"{'='*80}\n")
    
    return analysis_results


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
        #ax.fill_between(df_daily_clean.index, df_daily_clean['min'], df_daily_clean['max'], alpha=0.3, color=color)
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
    if legend_labels:
        ax.legend(lines, legend_labels, bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)
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
        ax.legend(handles[:len(legend_labels)], legend_labels, bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)
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

    # Farbe für Achsen und Beschriftungen
    axis_color = (0/255, 20/255, 80/255)
    
    ax.set_xlabel('Tag und Datum', fontsize=14, color=axis_color)
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
    if legend_labels and lines:
        ax.legend(lines, legend_labels, bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)
    elif lines:
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

    lines = []
    for idx, column in enumerate(columns):
        # Stündliche Aggregation
        df_hourly = month_data[column].resample('H').agg(['mean', 'min', 'max'])

        # Ensure data is numeric and drop NaN values
        df_hourly_clean = df_hourly.dropna().apply(pd.to_numeric, errors='coerce')
        if df_hourly_clean.empty:
            print(f"Warnung: Keine gültigen stündlichen Daten für Spalte '{column}' im gewählten Monat.")
            continue

        # Farbe aus cd_palette verwenden
        color = cd_palette[idx % len(cd_palette)]

        ax.fill_between(df_hourly_clean.index, df_hourly_clean['min'], df_hourly_clean['max'], alpha=0.3, color=color)
        line, = ax.plot(df_hourly_clean.index, df_hourly_clean['mean'], label=column, color=color, linewidth=2)
        lines.append(line)

    # Farbe für Achsen und Beschriftungen
    axis_color = (0/255, 20/255, 80/255)
    
    ax.set_xlabel('Datum', fontsize=14, color=axis_color)
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
    if legend_labels and lines:
        ax.legend(lines, legend_labels, bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=3, fontsize=14, labelcolor=axis_color)
    elif lines:
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
selected_columns =      ['Batterie_stand [%]', 'Pumpspeicher_stand [%]', 'H2_Speicher_stand [%]']
custom_labels =     ['Batteriespeicher SOC', 'Pumpspeicher SOC', 'Wasserstoffspeicher SOC']


title =                 'Ladezustand der Speicher im Jahresgang 2023'
ylabel =                'Ladezustand in %'
#highlight_date=         '2023-11-30'


fig, ax = plot_daily_aggregation(df, selected_columns, 
                                 None,  # Kein spezifisches Datum hervorgehoben
                                 title, 
                                 ylabel,
                                 legend_labels=custom_labels)

# Auswertung für Jahresgang
analysis_year = analyze_data(df, selected_columns, time_period='Jahresgang 2023 (Speicher)', period_data=df)

# Speichern der Figur
plt.savefig(f'data/c_Auswertung/{df_name}_{title}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben








# Beispielaufruf für die Darstellung eines spezifischen Tages
selected_days =                         ['2023-12-04']
# selected_columns =                       ['EMobilität', 'Wärmepumpen']
# custom_labels =                         ['Netzlast', 'modellierter Verbrauch']
title=                                  f'Ladezustand der Speicher am {selected_days[0]}'
ylabel=                                 'Ladezustand in %'

fig, ax = plot_selected_days(df, selected_columns, selected_days, 
                   None,  # Hervorheben des Werts um 08:45 Uhr
                   title, 
                   ylabel,
                   legend_labels=custom_labels)

# Auswertung für spezifischen Tag
day_data = df[df.index.date == pd.to_datetime(selected_days[0]).date()]
analysis_day = analyze_data(df, selected_columns, time_period=f'Tag {selected_days[0]} (Speicher)', period_data=day_data)

plt.savefig(f'data/c_Auswertung/{df_name}_{selected_days}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

# Beispielaufruf für die Darstellung einer Woche
week_start =                            '2023-12-01'  # Startdatum der Woche
# selected_columns =                       ['EMobilität', 'Wärmepumpen']
# custom_labels =                         ['Netzlast', 'Modellierung']
title =                                 f'Ladezustand der Speicher für die Woche ab {week_start}'
ylabel =                                'Ladezustand in %'

fig, ax = plot_weekly_aggregation(df, selected_columns, week_start,
                                  title, 
                                  ylabel,
                                  legend_labels=custom_labels)

# Auswertung für die Woche
week_start_dt = pd.to_datetime(week_start)
week_end_dt = week_start_dt + pd.Timedelta(days=6)
week_data = df[(df.index >= week_start_dt) & (df.index <= week_end_dt)]
analysis_week = analyze_data(df, selected_columns, time_period=f'Woche ab {week_start} (Speicher)', period_data=week_data)

plt.savefig(f'data/c_Auswertung/{df_name}_{week_start}.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

# Beispielaufruf für die Darstellung eines Monats
month_start =                           '2023-12-01'  # Startdatum des Monats
#selected_columns =                       ['EMobilität', 'Wärmepumpen']
#custom_labels =                         ['Netzlast', 'Modellierung']
title =                                 f'Ladezustand der Speicher für den Monat {pd.to_datetime(month_start).strftime("%B %Y")}'
ylabel =                                'Ladezustand in %'

fig, ax = plot_monthly_aggregation(df, selected_columns, month_start,
                                   title, 
                                   ylabel,
                                   legend_labels=custom_labels)

# Auswertung für den Monat
month_start_dt = pd.to_datetime(month_start)
if month_start_dt.month == 12:
    month_end_dt = month_start_dt.replace(year=month_start_dt.year + 1, month=1, day=1) - pd.Timedelta(days=1)
else:
    month_end_dt = month_start_dt.replace(month=month_start_dt.month + 1, day=1) - pd.Timedelta(days=1)
month_end_dt = month_end_dt.replace(hour=23, minute=59, second=59)
month_data = df[(df.index >= month_start_dt) & (df.index <= month_end_dt)]
analysis_month = analyze_data(df, selected_columns, 
                              time_period=f'Monat {pd.to_datetime(month_start).strftime("%B %Y")} (Speicher)', 
                              period_data=month_data)

plt.savefig(f'data/c_Auswertung/{df_name}_{month_start}_month.png', dpi=300, bbox_inches='tight')
plt.close(fig)  # Schließt die Figur, um Ressourcen freizugeben

print("Grafiken wurden erfolgreich erstellt und gespeichert.")