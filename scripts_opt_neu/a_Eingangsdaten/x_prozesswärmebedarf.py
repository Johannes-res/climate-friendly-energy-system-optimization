from datetime import datetime
import pandas as pd
import numpy as np
from matplotlib.ticker import FuncFormatter

# Zeitraum definieren
start = datetime(2023, 1, 1)
end = datetime(2023, 12, 31)

# Prozesswärmebedarf für das Jahr 2023 in GWh (Beispielwert, bitte anpassen)
PWB_a = 400e3  # Beispielwert für Industrie, bitte anpassen

# Erstellt einen DataFrame mit konstantem Prozesswärmebedarf pro Tag, verteilt über das Jahr
date_range = pd.date_range(start=start, end=end, freq='D')
df = pd.DataFrame(index=date_range)
df['Prozesswärmebedarf [GWh]'] = PWB_a / len(date_range)  # Gleichmäßige Verteilung

# Ergebnis in eine Excel-Datei speichern
df.to_excel(r'data\a_Eingangsdaten\Wärme\Prozesswärmebedarf_täglich_23.xlsx')

# tägliche Schwankungen innerhalb der Kernarbeitszeit einbauen (mit Gauß-Glättung)
def expand_daily_to_15min_with_workhours(df_daily,
                                         value_col='Prozesswärmebedarf [GWh]',
                                         work_start='08:00',
                                         work_end='17:00',
                                         work_multiplier=1.1,
                                         smooth_hours=2.0):
    """
    Erzeugt eine 15-Minuten-Zeitreihe aus täglichen Werten.
    Innerhalb der Kernarbeitszeit (work_start..work_end) wird der Bedarf um
    den Faktor work_multiplier erhöht; außerhalb wird der Basiswert verwendet.
    Die Gewichte werden anschließend mit einem gaußschen Filter geglättet
    (smooth_hours steuert die Breite der Glättung in Stunden), so dass Anstieg
    und Abfall flacher über einen längeren Zeitraum erfolgen.
    Rückgabe: DataFrame mit 15-Minuten-Index und Spalte value_col.
    """
    df_daily = df_daily.copy()
    df_daily.index = pd.to_datetime(df_daily.index).normalize()

    # Template 15-min index für einen Tag
    day_idx = pd.date_range(start='00:00', end='23:45', freq='15T').time
    n_per_day = len(day_idx)  # sollte 96 sein

    # Maske für Arbeitszeit innerhalb des Tagestemplate
    work_start_t = pd.to_datetime(work_start).time()
    work_end_t = pd.to_datetime(work_end).time()

    # Erstelle Gewichtungs-Array (Basis=1, Arbeitszeit = work_multiplier)
    weights_template = np.ones(n_per_day, dtype=float)
    if work_start_t <= work_end_t:
        mask = [(t >= work_start_t) and (t < work_end_t) for t in day_idx]
    else:
        mask = [(t >= work_start_t) or (t < work_end_t) for t in day_idx]
    weights_template = np.where(mask, work_multiplier, 1.0)

    # Gauß-Glättung der Gewichtung (optional, smooth_hours in Stunden)
    if smooth_hours is not None and smooth_hours > 0:
        # sigma in Slots (4 Slots pro Stunde)
        sigma_slots = smooth_hours * 4.0
        # Radius so wählen, dass Kernel ausreichend breit ist
        radius = max(1, int(np.ceil(4 * sigma_slots)))
        x = np.arange(-radius, radius + 1)
        kernel = np.exp(-0.5 * (x / sigma_slots) ** 2)
        kernel = kernel / kernel.sum()
        # Um Randeffekte und Übergänge über Mitternacht zu behandeln, tile 3x und dann mittleren Teil nehmen
        ext = np.tile(weights_template, 3)
        conv_ext = np.convolve(ext, kernel, mode='same')
        smoothed = conv_ext[n_per_day:2 * n_per_day]
        weights_template = smoothed.astype(float)

    rows = []
    for day, row in df_daily.iterrows():
        day_total = float(row[value_col])
        # Normiere Gewichte so dass Sum(weights) = 1 (über Slots)
        norm = weights_template.sum()
        slot_values = day_total * (weights_template / norm)
        timestamps = [pd.Timestamp.combine(day, t) for t in day_idx]
        rows.append(pd.DataFrame({value_col: slot_values}, index=timestamps))

    df_15 = pd.concat(rows)
    df_15.index = pd.to_datetime(df_15.index)
    return df_15

# Beispiel: erhöhe Bedarf während 08:00-17:00 um 50%
df_15min_weighted = expand_daily_to_15min_with_workhours(
    df,
    value_col='Prozesswärmebedarf [GWh]',
    work_start='07:00',
    work_end='16:00',
    work_multiplier=1.1,
    smooth_hours=2.0)

# Speichern (separat vom gleichmäßigen 15-min-File)
df_15min_weighted.to_excel(r'data\a_Eingangsdaten\Wärme\Prozesswärmebedarf_15min_23_weighted.xlsx')




# Plot Linie: Datum vs Raumwärmebedarf (design angelehnt an x_plot_bubble_chart_2.py)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Plot Linie: Datum vsE_mobbedarf (design angelehnt an x_plot_bubble_chart_2.py)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Daten für das Plot vorbereiten
df_plot = df_15min_weighted.copy()
df_plot.index = pd.to_datetime(df_plot.index)

#Ausschnitt einer Woche für das Plotten
df_plot = df_plot['2023-07-31':'2023-08-06']

fig, ax = plt.subplots(figsize=(12, 6))

plot_color = '#001450'  # gewünschter Farbcode für Linie und Beschriftungen
text_color = plot_color

# Linie mit kleinen Markern (keine Füllung)
ax.plot(
    df_plot.index,
    df_plot['Prozesswärmebedarf [GWh]'],
    color=plot_color,
    linewidth=2,
    marker='o',
    markersize=4,
    alpha=0.95,
    label='Prozesswärmebedarf in GWh'
)

# Hintergrund weiß
ax.set_facecolor('white')
fig.patch.set_facecolor('white')

# Nur horizontale Gitternetzlinien
ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
ax.grid(False, axis='x')  # sicherstellen, dass keine vertikalen Gitternetzlinien gezeichnet werden

# Styling (ähnlich wie x_plot_bubble_chart_2.py) — Farben auf #001450 setzen
ax.set_title('modellierter Prozesswärmebedarf 2023', fontsize=14, fontweight='bold', color=text_color)
ax.set_xlabel('Datum', fontsize=12, color=text_color)
ax.set_ylabel('Prozesswärmebedarf in GWh', fontsize=12, color=text_color)

# Y-Achse bei 0 beginnen lassen
ax.set_ylim(bottom=0)

# Datumsformatierung: Stunden auf der x-Achse (ein Tick pro Stunde)
ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))  # jeden Tag ein Major-Tick
ax.xaxis.set_minor_locator(mdates.HourLocator(interval=2))  # alle 2 Stunden ein Minor-Tick
de_days = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']

def german_date_formatter(x, pos=None):
    dt = mdates.num2date(x)
    day = de_days[dt.weekday()]
    return f"{day} {dt.day:02d}.{dt.month:02d} {dt.hour:02d}:{dt.minute:02d}"

ax.xaxis.set_major_formatter(FuncFormatter(german_date_formatter))
plt.setp(ax.get_xticklabels(), rotation=45, ha='right', color=text_color)
plt.setp(ax.get_yticklabels(), color=text_color)

# Achsenränder ebenfalls einfärben
for spine in ax.spines.values():
    spine.set_color(text_color)

# Legende einfärben
leg = ax.legend(frameon=False)
for text in leg.get_texts():
    text.set_color(text_color)

# Achsenticks einfärben
ax.tick_params(axis='x', colors=text_color)
ax.tick_params(axis='y', colors=text_color)

# --- Pfeile an die Achsen setzen ---
# Grenzen holen und leicht erweitern, damit die Pfeilspitzen sichtbar sind
x_min, x_max = ax.get_xlim()
y_min, y_max = ax.get_ylim()
x_range = x_max - x_min if x_max != x_min else 1.0
y_range = y_max - y_min if y_max != y_min else 1.0

x_pad = 0.03 * x_range
y_pad = 0.05 * y_range

# Neue Grenzen setzen (erweitert nach oben/rechts)
ax.set_xlim(x_min, x_max + x_pad)
ax.set_ylim(y_min, y_max + y_pad)

# X-Achsenpfeil (von links nach rechts)
ax.annotate(
    '',
    xy=(x_max + x_pad, y_min),
    xytext=(x_min, y_min),
    arrowprops=dict(arrowstyle='->', color=text_color, linewidth=1.5, mutation_scale=12),
    clip_on=False
)

# Y-Achsenpfeil (von unten nach oben)
ax.annotate(
    '',
    xy=(x_min, y_max + y_pad),
    xytext=(x_min, y_min),
    arrowprops=dict(arrowstyle='->', color=text_color, linewidth=1.5, mutation_scale=12),
    clip_on=False
)
# --- Ende Pfeile ---

plt.tight_layout()

# Grafik speichern
plt.savefig(r'data\a_Eingangsdaten\Wärme\Prozesswärmebedarf_15min_Woche_23_a_plot.png', dpi=150)
plt.close(fig)

def expand_daily_to_15min(df_daily, value_col='Prozesswärmebedarf [GWh]'):
    """
    Erweitert ein tägliches DataFrame zu einer 15-Minuten-Zeitreihe.
    Der Tageswert in `value_col` wird gleichmäßig auf 96 Intervalle verteilt.
    Rückgabe: DataFrame mit 15-min Index und gleicher Spaltenbezeichnung.
    """
    df_daily = df_daily.copy()
    df_daily.index = pd.to_datetime(df_daily.index)  # sicherstellen, dass Index datetime ist

    # 15-Minuten-Index vom ersten bis zum letzten Tag (inklusive letzter Tag 23:45)
    start = df_daily.index.min()
    end = df_daily.index.max() + pd.Timedelta(days=1) - pd.Timedelta(minutes=15)
    idx_15 = pd.date_range(start=start, end=end, freq='15T')

    # Tageswerte normalisieren (Datum ohne Uhrzeit)
    day_vals = df_daily[value_col].copy()
    day_vals.index = day_vals.index.normalize()

    # Für jeden 15-min-Zeitpunkt den zugehörigen Tageswert holen und durch 96 teilen
    day_index_for_15 = idx_15.normalize()
    values_15 = day_vals.reindex(day_index_for_15).values / 96.0  # 96 * 15min = 1 Tag

    series_15 = pd.Series(data=values_15, index=idx_15, name=value_col)
    df_15 = series_15.to_frame()

    return df_15

# Erzeuge 15-Minuten-Zeitreihen und speichern
# df_15min = expand_daily_to_15min(df, value_col='Prozesswärmebedarf [GWh]')
# df_15min.to_excel(r'data\a_Eingangsdaten\Wärme\Prozesswärmebedarf_15min_23.xlsx')




print('Prozesswärmebedarf skript beendet')