from meteostat import Stations, Daily
from datetime import datetime
import pandas as pd

# Zeitraum definieren
start = datetime(2023, 1, 1)
end = datetime(2023, 12, 31)

# Raumwärmebedarf für das Jahr 2023 in kWh (Beispielwert, bitte anpassen)
RWB_a = 150e3  # Beispielwert, bitte anpassen

# Wetterstationen in Deutschland auswählen (z.B. 50 zufällige Stationen)
stations = Stations().region('DE').inventory('daily', (start, end)).fetch(limit=100, sample=True)

# Tageswerte laden und räumlich mitteln
weather = Daily(stations, start, end)
df = weather.aggregate('1D', spatial=True).fetch()

# Die Spalte 'tavg' enthält die gemittelte Tagesdurchschnittstemperatur
print(df[['tavg']])

#ändert das dateformat in datetime auf werte ohne Zeitumstellung
df.index = df.index.tz_localize('UTC')
df.index = df.index.strftime('%Y-%m-%d')



# Alle weiteren Werte ausser tavg entfernen
df = df[['tavg']]
# sicherstellen, dass 'tavg' numerisch ist (optional)
df['tavg'] = pd.to_numeric(df['tavg'], errors='coerce')

# wenn tavg <= 15, dann 20 - tavg, sonst 0
df['Gradtagzahl'] = (20 - df['tavg']).where(df['tavg'] <= 15, 0)

# Werte, welche zwischen dem 1.5. und 30.9. liegen, auf 0 setzen
df.loc[(df.index >= '2023-05-01') & (df.index <= '2023-09-30'), 'Gradtagzahl'] = 0

#Gradtagzahlen durch die Summe der Gradtagzahlen teilen.
df['Raumwärmebedarf [GWh]'] = df['Gradtagzahl'] / df['Gradtagzahl'].sum() * RWB_a


# Ergebnis in eine Excel-Datei speichern
df.to_excel(r'data\Wetterdaten\durchschnitt_täglich_23_a.xlsx')

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

plt.tight_layout()

# Grafik speichern
plt.savefig(r'data\Wetterdaten\durchschnitt_täglich_23_a_plot.png', dpi=150)
plt.close(fig)

print('meteostat skript beendet')