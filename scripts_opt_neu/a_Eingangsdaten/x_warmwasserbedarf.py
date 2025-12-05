from meteostat import Stations, Daily
from datetime import datetime
import pandas as pd
import numpy as np
from x_raumwärmebedarf import df as df_tavg

df_tavg = df_tavg[['tavg']].copy()

# Zeitraum definieren
start = datetime(2023, 1, 1)
end = datetime(2023, 12, 31)

# Warmwasserbedarf für das Jahr 2023 in GWh (Beispielwert, bitte anpassen)
WWB_a = 97e3  # WWB_Gebäude 2023 in GWh

# Erstellt einen DataFrame mit konstantem Warmwasserbedarf pro Tag, variiert durch eine saisonale Sinusfunktion (±10%),
# mit Minimum im Sommer (Juni/Juli/August) und Maximum im Winter (Dezember/Januar/Februar).

# Tagesindex für das Jahr
dates = pd.date_range(start=start, end=end, freq='D')

# Anzahl Tage im Jahr (inklusive beider Endpunkte)
days_in_year = (end - start).days + 1

# Basis: jährlicher Warmwasserbedarf WWB_a 
annual_gwh = WWB_a 
daily_base_gwh = annual_gwh / days_in_year

# Saisonschwankung: ±10% um den Mittelwert, Minimum ~ Mitte Juli, Maximum ~ Mitte Januar
amplitude = 0.10  # ±10%
# Wähle Phase so, dass cos(...) = 1 ~ Mitte Januar und = -1 ~ Mitte Juli
phase_day = pd.Timestamp(datetime(start.year, 1, 15)).dayofyear

doy = dates.dayofyear.values
seasonal_factor = 1.0 + amplitude * np.cos(2 * np.pi * (doy - phase_day) / 365.0)

# Tageswerte in GWh
daily_values_gwh = daily_base_gwh * seasonal_factor

# DataFrame erstellen mit erwarteter Spaltenbezeichnung
df = pd.DataFrame({'Warmwasserbedarf [GWh]': daily_values_gwh}, index=dates)
df['Warmwasserbedarf [MWh]'] = df['Warmwasserbedarf [GWh]'] * 1000.0  # in MWh

wwb=df.copy()

wwb.index = wwb.index.tz_localize('UTC')
wwb.index = wwb.index.strftime('%Y-%m-%d')
# Ergebnis in eine Excel-Datei speichern
df_wwb.to_excel(r'data\a_Eingangsdaten\Wärme\Warmwasserbedarf_täglich_23.xlsx')



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
    df_plot['Warmwasserbedarf [GWh]'],
    color=plot_color,
    linewidth=2,
    marker='o',
    markersize=4,
    alpha=0.95,
    label='Warmwasserbedarf'
)

# Hintergrund weiß
ax.set_facecolor('white')
fig.patch.set_facecolor('white')

# Nur horizontale Gitternetzlinien
ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
ax.grid(False, axis='x')  # sicherstellen, dass keine vertikalen Gitternetzlinien gezeichnet werden

# Styling (ähnlich wie x_plot_bubble_chart_2.py) — Farben auf #001450 setzen
ax.set_title('modellierter Warmwasserbedarf 2023', fontsize=14, fontweight='bold', color=text_color)
ax.set_xlabel('Datum', fontsize=12, color=text_color)
ax.set_ylabel('Warmwasserbedarf [GWh]', fontsize=12, color=text_color)

# Y-Achse bei 0 beginnen lassen
ax.set_ylim(bottom=0)

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
plt.savefig(r'data\a_Eingangsdaten\Wärme\Warmwasserbedarf_täglich_23_a_plot.png', dpi=150)
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
    if value_col == 'Strombedarf_Warmwasser [GW]':
        values_15 = day_vals.reindex(day_index_for_15).values  # Leistung bleibt konstant
    else:
        values_15 = day_vals.reindex(day_index_for_15).values / 96.0  # 96 * 15min = 1 Tag

    series_15 = pd.Series(data=values_15, index=idx_15, name=value_col)
    df_15 = series_15.to_frame()

    return df_15


df_strom=bedarf_mit_strom_decken(df_wwb,df_tavg)

df_15min = expand_daily_to_15min(df_strom, value_col='Strombedarf_Warmwasser [GW]')

df_15min.to_excel(r'data\a_Eingangsdaten\Wärme\Warmwasser_Strombedarf_15min_23.xlsx')









# # Plot Linie: Datum vs Raumwärmebedarf (design angelehnt an x_plot_bubble_chart_2.py)
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates

# # Daten für das Plot vorbereiten
# df_plot = df_wwb.copy()
# df_plot.index = pd.to_datetime(df_plot.index)

# fig, ax = plt.subplots(figsize=(12, 6))

# plot_color = '#001450'  # gewünschter Farbcode für Linie und Beschriftungen
# text_color = plot_color

# # Linie mit kleinen Markern (keine Füllung)
# ax.plot(
#     df_plot.index,
#     df_plot['Warmwasserbedarf [GWh]'],
#     color=plot_color,
#     linewidth=2,
#     marker='o',
#     markersize=4,
#     alpha=0.95,
#     label='Warmwasserbedarf'
# )

# # Hintergrund weiß
# ax.set_facecolor('white')
# fig.patch.set_facecolor('white')

# # Nur horizontale Gitternetzlinien
# ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
# ax.grid(False, axis='x')  # sicherstellen, dass keine vertikalen Gitternetzlinien gezeichnet werden

# # Styling (ähnlich wie x_plot_bubble_chart_2.py) — Farben auf #001450 setzen
# ax.set_title('modellierter Warmwasserbedarf 2023', fontsize=14, fontweight='bold', color=text_color)
# ax.set_xlabel('Datum', fontsize=12, color=text_color)
# ax.set_ylabel('Warmwasserbedarf [GWh]', fontsize=12, color=text_color)

# # Y-Achse bei 0 beginnen lassen
# ax.set_ylim(bottom=0)

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
# plt.savefig(r'data\a_Eingangsdaten\Wärme\Warmwasserbedarf_täglich_23_a_plot.png', dpi=150)
# plt.close(fig)



# Erzeuge 15-Minuten-Zeitreihen und speichern
df_15min_wwb = expand_daily_to_15min(df_wwb, value_col='Warmwasserbedarf [GWh]')
df_15min_wwb['Last_Warmwasser [GW]'] = df_15min_wwb['Warmwasserbedarf [GWh]'] *4  # Umrechnung in GW
df_15min_wwb.to_excel(r'data\a_Eingangsdaten\Wärme\Warmwasserbedarf_15min_23.xlsx')

#ggf. kann hier noch eine Tag-Nacht-Wichtung eingebaut werden

#%%

print('Warmwasserbedarf skript beendet')