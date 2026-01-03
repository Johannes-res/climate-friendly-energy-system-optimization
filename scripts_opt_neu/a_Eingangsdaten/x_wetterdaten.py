from meteostat import Stations, Daily
from datetime import datetime
import pandas as pd

def durchschnittstemperatur_ermitteln(jahr, anzahl_wetterstationen):

        # Zeitraum definieren
    jahr=jahr
    start = datetime(jahr, 1, 1)
    end = datetime(jahr, 12, 31)

    # Wetterstationen in Deutschland auswählen (z.B. 50 zufällige Stationen)
    stations = Stations().region('DE').inventory('daily', (start, end)).fetch(limit=anzahl_wetterstationen, sample=True)

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
    df.loc[(df.index >= f'{jahr}-05-01') & (df.index <= f'{jahr}-09-30'), 'Gradtagzahl'] = 0



    # Ergebnis in eine Excel-Datei speichern
    df.to_excel(f'data\Wetterdaten\durchschnitt_täglich_{jahr}.xlsx')

    return df

df_23 = durchschnittstemperatur_ermitteln(2023, 100)
df_22= durchschnittstemperatur_ermitteln(2022, 100)
df_24 = durchschnittstemperatur_ermitteln(2024, 100)

print('meteostat skript beendet')