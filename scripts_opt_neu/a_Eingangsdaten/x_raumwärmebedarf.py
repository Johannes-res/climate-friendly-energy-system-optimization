from meteostat import Stations, Daily
from datetime import datetime
import pandas as pd
import os
from pathlib import Path

# # Zeitraum definieren
# start = datetime(2023, 1, 1)
# end = datetime(2023, 12, 31)

# # Raumwärmebedarf für das Jahr 2023 
# RWB_a = 431e3  # Raumwärmebedarf Gebäude 2023 in GWh

# # Wetterstationen in Deutschland auswählen (z.B. 50 zufällige Stationen)
# stations = Stations().region('DE').inventory('daily', (start, end)).fetch(limit=100, sample=True)

# # Tageswerte laden und räumlich mitteln
# weather = Daily(stations, start, end)
# df = weather.aggregate('1D', spatial=True).fetch()

# # Die Spalte 'tavg' enthält die gemittelte Tagesdurchschnittstemperatur
# print(df[['tavg']])

# #ändert das dateformat in datetime auf werte ohne Zeitumstellung
# df.index = df.index.tz_localize('UTC')
# df.index = df.index.strftime('%Y-%m-%d')



# # Alle weiteren Werte ausser tavg entfernen
# df = df[['tavg']]
# # sicherstellen, dass 'tavg' numerisch ist (optional)
# df['tavg'] = pd.to_numeric(df['tavg'], errors='coerce')

# # wenn tavg <= 15, dann 20 - tavg, sonst 0
# df['Gradtagzahl'] = (20 - df['tavg']).where(df['tavg'] <= 15, 0)

# # Werte, welche zwischen dem 1.5. und 30.9. liegen, auf 0 setzen
# df.loc[(df.index >= '2023-05-01') & (df.index <= '2023-09-30'), 'Gradtagzahl'] = 0

# #Gradtagzahlen durch die Summe der Gradtagzahlen teilen.
# df['Raumwärmebedarf [GWh]'] = df['Gradtagzahl'] / df['Gradtagzahl'].sum() * RWB_a

df['Raumwärmebedarf [MWh]'] = df['Raumwärmebedarf [GWh]'] * 1000.0  # in MWh
rwb = df['Raumwärmebedarf [MWh]'].copy()
# Ergebnis in eine Excel-Datei speichern
df.to_excel(r'data\a_Eingangsdaten\Wärme\Raumwärmebedarf_täglich_23.xlsx')


#%% Grafik
# Plot Linie: Datum vs Raumwärmebedarf (design angelehnt an x_plot_bubble_chart_2.py)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Daten für das Plot vorbereiten
df_plot = df.copy()
df_plot.index = pd.to_datetime(df_plot.index)

fig, ax = plt.subplots(figsize=(12, 6))

plot_color = '#001450'  # gewünschter Farbcode für Linie und Beschriftungen
text_color = plot_color

# Linie mit kleinen Markern (keine Füllung)
ax.plot(
    df_plot.index,
    df_plot['Raumwärmebedarf [GWh]'],
    color=plot_color,
    linewidth=2,
    marker='o',
    markersize=4,
    alpha=0.95,
    label='Raumwärmebedarf'
)

# Hintergrund weiß
ax.set_facecolor('white')
fig.patch.set_facecolor('white')

# Nur horizontale Gitternetzlinien
ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
ax.grid(False, axis='x')  # sicherstellen, dass keine vertikalen Gitternetzlinien gezeichnet werden

# Styling (ähnlich wie x_plot_bubble_chart_2.py) — Farben auf #001450 setzen
ax.set_title('modellierter Raumwärmebedarf 2023', fontsize=14, fontweight='bold', color=text_color)
ax.set_xlabel('Datum', fontsize=12, color=text_color)
ax.set_ylabel('Raumwärmebedarf [GWh]', fontsize=12, color=text_color)

# Datumsformatierung: Monatsnamen auf der x-Achse
ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
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
plt.savefig(r'data\a_Eingangsdaten\Wärme\Raumwärmebedarf_täglich_23_a_plot.png', dpi=150)
plt.close(fig)

def expand_daily_to_15min(df_daily, value_col='Raumwärmebedarf [GWh]'):
    """
    Erweitert ein tägliches DataFrame zu einer 15-Minuten-Zeitreihe.
    - Bei 'Raumwärmebedarf [GWh]' wird der Tageswert gleichmäßig auf 96 Intervalle verteilt.
    - Bei 'Strombedarf_Raumwärme [GW]' bleibt die Leistung konstant (kein Teilen durch 96).
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

    # Für jeden 15-min-Zeitpunkt den zugehörigen Tageswert holen
    day_index_for_15 = idx_15.normalize()
    
    # Bei Leistung (GW) nicht teilen, bei Energie (GWh) durch 96 teilen
    if value_col == 'Strombedarf_Raumwärme [GW]':
        values_15 = day_vals.reindex(day_index_for_15).values  # Leistung bleibt konstant
    else:
        values_15 = day_vals.reindex(day_index_for_15).values / 96.0  # 96 * 15min = 1 Tag

    series_15 = pd.Series(data=values_15, index=idx_15, name=value_col)
    df_15 = series_15.to_frame()

    return df_15



df_strom = raumwärme_mit_strom_decken(df)

df_strom_15min = expand_daily_to_15min(df_strom, value_col='Strombedarf_Raumwärme [GW]')

df_strom_15min.to_excel(r'data\a_Eingangsdaten\Wärme\Raumwärme_Strombedarf_15min_23.xlsx')















# # Plot Linie: Datum vs Raumwärmebedarf (design angelehnt an x_plot_bubble_chart_2.py)
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates

# #%% Daten für das Plot vorbereiten
# df_plot = df.copy()
# df_plot.index = pd.to_datetime(df_plot.index)

# fig, ax = plt.subplots(figsize=(12, 6))

# plot_color = '#001450'  # gewünschter Farbcode für Linie und Beschriftungen
# text_color = plot_color

# # Linie mit kleinen Markern (keine Füllung)
# ax.plot(
#     df_plot.index,
#     df_plot['Raumwärmebedarf [GWh]'],
#     color=plot_color,
#     linewidth=2,
#     marker='o',
#     markersize=4,
#     alpha=0.95,
#     label='Raumwärmebedarf'
# )

# # Hintergrund weiß
# ax.set_facecolor('white')
# fig.patch.set_facecolor('white')

# # Nur horizontale Gitternetzlinien
# ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
# ax.grid(False, axis='x')  # sicherstellen, dass keine vertikalen Gitternetzlinien gezeichnet werden

# # Styling (ähnlich wie x_plot_bubble_chart_2.py) — Farben auf #001450 setzen
# ax.set_title('modellierter Raumwärmebedarf 2023', fontsize=14, fontweight='bold', color=text_color)
# ax.set_xlabel('Datum', fontsize=12, color=text_color)
# ax.set_ylabel('Raumwärmebedarf [GWh]', fontsize=12, color=text_color)

# # Datumsformatierung: Monatsnamen auf der x-Achse
# ax.xaxis.set_major_locator(mdates.MonthLocator())
# ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
# plt.setp(ax.get_xticklabels(), rotation=45, ha='right', color=text_color)
# plt.setp(ax.get_yticklabels(), color=text_color)

# # Achsenränder ebenfalls einfärben
# for spine in ax.spines.values():
#     spine.set_color(text_color)

# # Legende einfärben
# leg = ax.legend(frameon=False)
# for text in leg.get_texts():
#     text.set_color(text_color)

# # Achsenticks einfärben
# ax.tick_params(axis='x', colors=text_color)
# ax.tick_params(axis='y', colors=text_color)


# # --- Pfeile an die Achsen setzen ---
# # Grenzen holen und leicht erweitern, damit die Pfeilspitzen sichtbar sind
# x_min, x_max = ax.get_xlim()
# y_min, y_max = ax.get_ylim()
# x_range = x_max - x_min if x_max != x_min else 1.0
# y_range = y_max - y_min if y_max != y_min else 1.0

# x_pad = 0.03 * x_range
# y_pad = 0.05 * y_range

# # Neue Grenzen setzen (erweitert nach oben/rechts)
# ax.set_xlim(x_min, x_max + x_pad)
# ax.set_ylim(y_min, y_max + y_pad)

# # X-Achsenpfeil (von links nach rechts)
# ax.annotate(
#     '',
#     xy=(x_max + x_pad, y_min),
#     xytext=(x_min, y_min),
#     arrowprops=dict(arrowstyle='->', color=text_color, linewidth=1.5, mutation_scale=12),
#     clip_on=False
# )

# # Y-Achsenpfeil (von unten nach oben)
# ax.annotate(
#     '',
#     xy=(x_min, y_max + y_pad),
#     xytext=(x_min, y_min),
#     arrowprops=dict(arrowstyle='->', color=text_color, linewidth=1.5, mutation_scale=12),
#     clip_on=False
# )
# # --- Ende Pfeile ---

# plt.tight_layout()



# # Grafik speichern
# plt.savefig(r'data\a_Eingangsdaten\Wärme\Raumwärmebedarf_täglich_23_a_plot.png', dpi=150)
# plt.close(fig)



# Erzeuge 15-Minuten-Zeitreihen und speichern
df_15min = expand_daily_to_15min(df, value_col='Raumwärmebedarf [GWh]')

df_15min['Last_Raumwärme [GW]'] = df_15min['Raumwärmebedarf [GWh]']*4


df_15min.to_excel(r'data\a_Eingangsdaten\Wärme\Raumwärmebedarf_15min_23.xlsx')

#ggf. kann hier noch eine Tag-Nacht-Wichtung eingebaut werden



print('Raumwärme skript beendet')