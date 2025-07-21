import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def weekly_to_daily_load(weekly_load=None, visualize=True):
    """
    Extrahiert tägliche Lastprofile aus einem wöchentlichen E-Mobilitäts-Lastprofil.
    
    Parameter:
    ----------
    weekly_load : array-like, optional
        Wöchentliches Lastprofil mit 168 Werten (stündliche Auflösung für eine Woche).
        Falls None, wird ein typisches Muster basierend auf dem Bild generiert.
    visualize : bool, default=True
        Ob die extrahierten Tagesprofile visualisiert werden sollen.
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame mit den täglichen Lastprofilen (Stunden als Index und Wochentage als Spalten).
    """
    days = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
    
    if weekly_load is None:
        # Generiere typisches E-Mobilitätslastmuster basierend auf dem Bildmuster
        hours = np.arange(0, 24)
        
        # Morgen- und Abendspitzen für Arbeitstage
        workday_pattern = 2 + 4 * np.exp(-0.5 * ((hours - 8) / 2) ** 2) + \
                          6 * np.exp(-0.5 * ((hours - 18) / 3) ** 2)
        
        # Verteiltes Muster für Wochenenden
        weekend_pattern = 1 + 2 * np.exp(-0.5 * ((hours - 10) / 3) ** 2) + \
                          4 * np.exp(-0.5 * ((hours - 16) / 3) ** 2)
        
        # Erstelle wöchentliche Daten mit Werktag/Wochenend-Muster
        daily_load_profiles = []
        for day in range(7):
            if day < 5:  # Werktag
                daily_load_profiles.append(workday_pattern)
            else:  # Wochenende
                daily_load_profiles.append(weekend_pattern)
    else:
        # Stelle sicher, dass der Input die richtige Form hat
        weekly_load = np.array(weekly_load).flatten()
        if len(weekly_load) != 168:
            raise ValueError("Wöchentliche Last muss 168 Werte enthalten (stündliche Auflösung für eine Woche).")
        
        # Extrahiere Tagesmuster aus den bereitgestellten Wochendaten
        daily_load_profiles = []
        for day in range(7):
            daily_load_profiles.append(weekly_load[day * 24:(day + 1) * 24])
    
    # Erstelle DataFrame mit passendem Index
    df = pd.DataFrame(index=range(24))
    
    for i, day_name in enumerate(days):
        df[day_name] = daily_load_profiles[i]
    
    # Benenne Index um, um Stunden darzustellen
    df.index.name = 'Stunde'
    
    # Visualisiere bei Bedarf
    if visualize:
        plt.figure(figsize=(12, 6))
        for i, day_name in enumerate(days):
            plt.plot(np.arange(0, 24), daily_load_profiles[i], label=day_name)
        
        plt.title('Tägliche Lastprofile für E-Mobilität')
        plt.xlabel('Stunde des Tages')
        plt.ylabel('Last (GW)')
        plt.legend()
        plt.grid(True)
        plt.xticks(np.arange(0, 24, 2))
        plt.show()
    
    return df

# Beispielaufruf der Funktion
lastprofile_df = weekly_to_daily_load()
print(lastprofile_df.head())