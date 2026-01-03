from datetime import datetime
import pandas as pd
import numpy as np
from matplotlib.ticker import FuncFormatter
import holidays

# Zeitraum definieren
start = datetime(2023, 1, 1)
end = datetime(2023, 12, 31)

# Prozesswärmebedarf für das Jahr 2023 in GWh (Beispielwert, bitte anpassen)
PWB_a = 40.5e3  # Gebäude und Fernwärme-Industrie in GWh

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
    - Werktage: Kernarbeitszeit (work_start..work_end) mit work_multiplier erhöht
    - Samstage: Bedarf um 20% gesenkt (Faktor 0.8)
    - Sonn-/Feiertage: Bedarf um 30% gesenkt (Faktor 0.7)
    Die Gewichte werden mit einem gaußschen Filter geglättet.
    Die Gesamtsumme über das Jahr bleibt konstant (Normierung).
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

    # Feiertage definieren
    de_holidays = holidays.Germany(years=[d.year for d in df_daily.index.unique()])

    # Schritt 1: Tagesskalierungsfaktoren bestimmen
    day_scale_factors = {}
    for timestamp in df_daily.index:
        if timestamp in de_holidays or timestamp.weekday() == 6:  # Sonn-/Feiertag
            day_scale_factors[timestamp] = 0.7  # 30% Reduktion
        elif timestamp.weekday() == 5:  # Samstag
            day_scale_factors[timestamp] = 0.8  # 20% Reduktion
        else:  # Werktag
            day_scale_factors[timestamp] = 1.0

    # Schritt 2: Normierungsfaktor berechnen, damit Gesamtsumme gleich bleibt
    original_sum = df_daily[value_col].sum()
    scaled_sum = sum(df_daily.loc[day, value_col] * day_scale_factors[day] 
                     for day in df_daily.index)
    norm_factor = original_sum / scaled_sum if scaled_sum > 0 else 1.0

    # Schritt 3: Gewichtungstemplate für Werktage erstellen (mit Arbeitszeit)
    weights_weekday = np.ones(n_per_day, dtype=float)
    if work_start_t <= work_end_t:
        mask = [(t >= work_start_t) and (t < work_end_t) for t in day_idx]
    else:
        mask = [(t >= work_start_t) or (t < work_end_t) for t in day_idx]
    weights_weekday = np.where(mask, work_multiplier, 1.0)

    # Gewichtungstemplate für Samstag und Sonntag (gleichmäßig)
    weights_saturday = np.ones(n_per_day, dtype=float)
    weights_sunday = np.ones(n_per_day, dtype=float)

    # Schritt 4: Gauß-Glättung auf alle Templates anwenden
    def smooth_weights(weights, smooth_hours):
        if smooth_hours is None or smooth_hours <= 0:
            return weights
        sigma_slots = smooth_hours * 4.0
        radius = max(1, int(np.ceil(4 * sigma_slots)))
        x = np.arange(-radius, radius + 1)
        kernel = np.exp(-0.5 * (x / sigma_slots) ** 2)
        kernel = kernel / kernel.sum()
        ext = np.tile(weights, 3)
        conv_ext = np.convolve(ext, kernel, mode='same')
        smoothed = conv_ext[n_per_day:2 * n_per_day]
        return smoothed.astype(float)

    weights_weekday = smooth_weights(weights_weekday, smooth_hours)
    weights_saturday = smooth_weights(weights_saturday, smooth_hours)
    weights_sunday = smooth_weights(weights_sunday, smooth_hours)

    # Schritt 5: Für jeden Tag die passende Gewichtung und Skalierung anwenden
    rows = []
    for day, row in df_daily.iterrows():
        day_total = float(row[value_col])
        
        # Tagesskalierung mit Normierung
        scaled_day_total = day_total * day_scale_factors[day] * norm_factor
        
        # Passende Gewichtung wählen
        if day in de_holidays or day.weekday() == 6:  # Sonn-/Feiertag
            weights = weights_sunday
        elif day.weekday() == 5:  # Samstag
            weights = weights_saturday
        else:  # Werktag
            weights = weights_weekday
        
        # Normiere Gewichte für diesen Tag
        norm = weights.sum()
        slot_values = scaled_day_total * (weights / norm)
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

df_15min_weighted ['Prozesswärmebedarf [GW]'] = df_15min_weighted['Prozesswärmebedarf [GWh]']*4  # Umrechnung in GW


# Speichern (separat vom gleichmäßigen 15-min-File)
df_15min_weighted.to_excel(r'data\a_Eingangsdaten\Wärme\Prozesswärmebedarf_15min_23_weighted.xlsx')



print("✓ Prozesswärmebedarf (15min, gewichtet) importiert")


# ...existing code (bis df_15min_weighted.to_excel)...

print("✓ Prozesswärmebedarf (15min, gewichtet) gespeichert:")
print(f"  - Spalten: {list(df_15min_weighted.columns)}")
print(f"  - Zeitraum: {df_15min_weighted.index.min()} bis {df_15min_weighted.index.max()}")
print(f"  - Anzahl Zeitpunkte: {len(df_15min_weighted)}")


# ========================================
# VISUALISIERUNGEN
# ========================================

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plot_color = '#001450'
text_color = plot_color

# ========================================
# 1. JAHRESANSICHT (Tägliche Werte)
# ========================================

# Tageswerte aus 15-min-Daten aggregieren
df_plot_year = df_15min_weighted.resample('1D').mean()
df_plot_year.index = pd.to_datetime(df_plot_year.index)

fig, ax = plt.subplots(figsize=(14, 6))

# Prozesswärmebedarf plotten
ax.plot(
    df_plot_year.index,
    df_plot_year['Prozesswärmebedarf [GW]'],
    color='#001450',
    linewidth=2,
    marker=None,
    markersize=3,
    alpha=0.95,
    label=None
)

# Styling
ax.set_facecolor('white')
fig.patch.set_facecolor('white')
ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
ax.grid(False, axis='x')

ax.set_title('modellierter Prozesswärmebedarf - Jahresübersicht', fontsize=14, fontweight='bold', color=text_color)
ax.set_xlabel('Monat', fontsize=12, color=text_color)
ax.set_ylabel('Leistung in GW', fontsize=12, color=text_color)

# Datumsformatierung: Monatsnamen
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
plt.setp(ax.get_xticklabels(), rotation=45, ha='right', color=text_color)
plt.setp(ax.get_yticklabels(), color=text_color)

# Achsen und Legende einfärben
for spine in ax.spines.values():
    spine.set_color(text_color)
leg = ax.legend(frameon=False, loc='upper right')
for text in leg.get_texts():
    text.set_color(text_color)
ax.tick_params(axis='both', colors=text_color)

# Pfeile an Achsen
x_min, x_max = ax.get_xlim()
y_min, y_max = ax.get_ylim()
x_range = x_max - x_min if x_max != x_min else 1.0
y_range = y_max - y_min if y_max != y_min else 1.0
x_pad = 0.02 * x_range
y_pad = 0.05 * y_range

ax.set_xlim(x_min, x_max + x_pad)
ax.set_ylim(y_min, y_max + y_pad)

ax.annotate('', xy=(x_max + x_pad, y_min), xytext=(x_min, y_min),
            arrowprops=dict(arrowstyle='->', color=text_color, linewidth=1.5, mutation_scale=12),
            clip_on=False)
ax.annotate('', xy=(x_min, y_max + y_pad), xytext=(x_min, y_min),
            arrowprops=dict(arrowstyle='->', color=text_color, linewidth=1.5, mutation_scale=12),
            clip_on=False)

plt.tight_layout()
plt.savefig(r'data\a_Eingangsdaten\Wärme\Prozesswärmebedarf_Jahresansicht_2023.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("✓ Jahresansicht gespeichert: Prozesswärmebedarf_Jahresansicht_2023.png")


# ========================================
# 2. WOCHENANSICHT (15-min-Werte)
# ========================================

week_start = pd.Timestamp('2023-01-09')
week_end = week_start + pd.Timedelta(days=7) - pd.Timedelta(minutes=15)

df_week = df_15min_weighted[(df_15min_weighted.index >= week_start) & (df_15min_weighted.index <= week_end)]

fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(
    df_week.index,
    df_week['Prozesswärmebedarf [GW]'],
    color='#001450',
    linewidth=2,
    alpha=0.95,
    label=None
)

# Styling
ax.set_facecolor('white')
fig.patch.set_facecolor('white')
ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
ax.grid(which='major', axis='x', color='#e6e6e6', linewidth=0.5, alpha=0.5)

ax.set_title(f'modellierter Prozesswärmebedarf - Wochenansicht ({week_start.strftime("%d.%m.")} - {week_end.strftime("%d.%m.%Y")})', 
             fontsize=14, fontweight='bold', color=text_color)
ax.set_xlabel('Datum', fontsize=12, color=text_color)
ax.set_ylabel('Leistung in GW', fontsize=12, color=text_color)

ax.xaxis.set_major_locator(mdates.DayLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%a\n%d.%m'))
ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
plt.setp(ax.get_xticklabels(), rotation=0, ha='center', color=text_color)
plt.setp(ax.get_yticklabels(), color=text_color)

# Achsen und Legende
for spine in ax.spines.values():
    spine.set_color(text_color)
leg = ax.legend(frameon=False, loc='upper right')
for text in leg.get_texts():
    text.set_color(text_color)
ax.tick_params(axis='both', colors=text_color)

# Pfeile
x_min, x_max = ax.get_xlim()
y_min, y_max = ax.get_ylim()
x_range = x_max - x_min if x_max != x_min else 1.0
y_range = y_max - y_min if y_max != y_min else 1.0
x_pad = 0.02 * x_range
y_pad = 0.05 * y_range

ax.set_xlim(x_min, x_max + x_pad)
ax.set_ylim(y_min, y_max + y_pad)

ax.annotate('', xy=(x_max + x_pad, y_min), xytext=(x_min, y_min),
            arrowprops=dict(arrowstyle='->', color=text_color, linewidth=1.5, mutation_scale=12),
            clip_on=False)
ax.annotate('', xy=(x_min, y_max + y_pad), xytext=(x_min, y_min),
            arrowprops=dict(arrowstyle='->', color=text_color, linewidth=1.5, mutation_scale=12),
            clip_on=False)

plt.tight_layout()
plt.savefig(r'data\a_Eingangsdaten\Wärme\Prozesswärmebedarf_Wochenansicht_2023.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("✓ Wochenansicht gespeichert: Prozesswärmebedarf_Wochenansicht_2023.png")


# ========================================
# 3. TAGESANSICHT (15-Minuten-Werte)
# ========================================

day_start = pd.Timestamp('2023-01-13')
day_end = day_start + pd.Timedelta(days=1) - pd.Timedelta(minutes=15)

df_day = df_15min_weighted[(df_15min_weighted.index >= day_start) & (df_15min_weighted.index <= day_end)]

fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(
    df_day.index,
    df_day['Prozesswärmebedarf [GW]'],
    color='#001450',
    linewidth=2,
    alpha=0.95,
    label=None
)

# Arbeitszeit-Bereich markieren (optional)
work_start = day_start + pd.Timedelta(hours=7)
work_end = day_start + pd.Timedelta(hours=16)
ax.axvspan(work_start, work_end, color='#001450', alpha=0.1, label='Kernarbeitszeit (7-16 Uhr)')

# Styling
ax.set_facecolor('white')
fig.patch.set_facecolor('white')
ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
ax.grid(which='major', axis='x', color='#e6e6e6', linewidth=0.5, alpha=0.5)

ax.set_title(f'modellierter Prozesswärmebedarf - Tagesansicht ({day_start.strftime("%d.%m.%Y")})', 
             fontsize=14, fontweight='bold', color=text_color)
ax.set_xlabel('Uhrzeit', fontsize=12, color=text_color)
ax.set_ylabel('Leistung in GW', fontsize=12, color=text_color)

# Datumsformatierung: Stündliche Ticks
ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=15))
plt.setp(ax.get_xticklabels(), rotation=45, ha='right', color=text_color)
plt.setp(ax.get_yticklabels(), color=text_color)

# Achsen und Legende
for spine in ax.spines.values():
    spine.set_color(text_color)
leg = ax.legend(frameon=False, loc='upper right')
for text in leg.get_texts():
    text.set_color(text_color)
ax.tick_params(axis='both', colors=text_color)

# Pfeile
x_min, x_max = ax.get_xlim()
y_min, y_max = ax.get_ylim()
x_range = x_max - x_min if x_max != x_min else 1.0
y_range = y_max - y_min if y_max != y_min else 1.0
x_pad = 0.02 * x_range
y_pad = 0.05 * y_range

ax.set_xlim(x_min, x_max + x_pad)
ax.set_ylim(y_min, y_max + y_pad)

ax.annotate('', xy=(x_max + x_pad, y_min), xytext=(x_min, y_min),
            arrowprops=dict(arrowstyle='->', color=text_color, linewidth=1.5, mutation_scale=12),
            clip_on=False)
ax.annotate('', xy=(x_min, y_max + y_pad), xytext=(x_min, y_min),
            arrowprops=dict(arrowstyle='->', color=text_color, linewidth=1.5, mutation_scale=12),
            clip_on=False)

plt.tight_layout()
plt.savefig(r'data\a_Eingangsdaten\Wärme\Prozesswärmebedarf_Tagesansicht_2023.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("✓ Tagesansicht gespeichert: Prozesswärmebedarf_Tagesansicht_2023.png")

print("\n✓ Alle 3 Visualisierungen erfolgreich erstellt!")
print("  1. Jahresansicht (täglich)")
print("  2. Wochenansicht (15-min, mit Wochenend-Effekt)")
print("  3. Tagesansicht (15-min, mit Kernarbeitszeit)")


print('Prozesswärmebedarf skript beendet')