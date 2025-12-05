from meteostat import Stations, Daily
from datetime import datetime
import pandas as pd

print("Teste Meteostat-Verbindung...")

try:
    # Zeitraum definieren
    start = datetime(2023, 1, 1)
    end = datetime(2023, 1, 7)  # Nur eine Woche zum Testen
    
    print(f"Suche Wetterstationen in Deutschland...")
    stations = Stations().region('DE').inventory('daily', (start, end)).fetch(limit=5)
    print(f"Gefunden: {len(stations)} Stationen")
    print(stations)
    
    print("\nLade Wetterdaten...")
    weather = Daily(stations, start, end)
    df = weather.aggregate('1D', spatial=True).fetch()
    
    print("\nErfolgreich! Erste Zeilen:")
    print(df.head())
    print(f"\nAnzahl Datensätze: {len(df)}")
    
except Exception as e:
    print(f"\nFehler: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\nTest abgeschlossen.")
