import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt

"""Dieses Skript dient zum Erstellen von Lastprofilen in Anlehnung der des BDEW.
Hierfür gibt es zunächst die Funktion 'def generiere_stufenfunktion', die mittels anpassbarer Stufen einen Tagesgang modelliert. Dazu muss die Uhrzeit und der Wert zu dieser festgelegt werden. Die festgelegten Punkte werden linear miteinander verbunden.
Zusätzlich kann der Abfall der letzten Stufe bestimmt werden (decay_rate). Mitteles 'smoothing_sigma' kann die Glättung der Kurve eingestellt werden, so dass keine harten Stufen mehr entstehen.
'def_auf_monate_erweitern' erweitert die Lastprofile auf monatliche Werte. Hierbei wird ein saisonaler Faktor berücksichtigt, der die Lastprofile an die Jahreszeiten anpasst. Es kann pro Monat ein Faktor festgelegt werden.
Die daraus für das Jahr entstehende Stufenfunktion wird in dem verknüften Skript 'last_prog_strom.py' bei Erstellen einer Jahreszeitreihe geglättet, so dass die Stufen verschwinden. Dies wird bewusst erst an dieser Stelle getan, um möglichst die Form der Standardlastprofile einzuhalten, auch wenn diese dann harte Sprünge in den Monaten aufweisen. --> Hier kann noch verbessert werden.
Die Funktion 'def_saisonale_schwankungen_modellieren' erstellt die saisonalen Faktoren für die einzelnen Monate mit Hilfe einer Cosinusfunktion."""
#%% wöchentliche Lastprofile in tägliche Lastprofile umwandeln
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

# Beispielnutzung mit Standardwerten
def plot_custom_load(df):
    plt.figure(figsize=(12, 6))
    
    for column in df.columns:
        plt.plot(df.index, df[column], label=f'Lastprofil {column}', linewidth=2)
    
    plt.title('E-Mobilitätslastprofile')
    plt.xlabel('Uhrzeit')
    plt.ylabel('Relative Last [0-1]')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

# plot_custom_load(df_Lastprofil_EMob)
# print("E-Mobilitätslastprofile erfolgreich generiert und dargestellt.")
# # Beispielaufruf der Funktion
# lastprofile_df = weekly_to_daily_load()
# print(lastprofile_df.head())

#%%Stufenfunktion für E-Mobilitätslastprofile
def generiere_stufenfunktion(profiles, decay_rate, smoothing_sigma=1.0):
    """
    Generiert mehrere stufenweise E-Mobilitätslastprofile als DataFrame mit Zeitindex und glättet die Ergebnisse.
    
    :param profiles: Ein Dictionary, bei dem die Schlüssel die Tagestypen sind (z. B. 'WT', 'SA') 
                     und die Werte Listen mit Stufenzeiten und Laststufen.
    :param decay_rate: Exponentieller Abfall nach der letzten Stufe.
    :param smoothing_sigma: Standardabweichung für die Gauß-Glättung (je größer, desto stärker die Glättung).
    :return: Ein DataFrame mit Zeitindex und einer Spalte pro Tagestyp.
    """
    # Zeitachse in 15-Minuten-Intervallen
    time = np.arange(0, 24, 0.25)
    date_range = pd.date_range(start="2023-01-01 00:00", periods=len(time), freq="15T")
    df = pd.DataFrame({'timestamp': date_range}).set_index('timestamp')

    for tagestyp, (stufenzeiten, laststufen) in profiles.items():
        # Validierung der Eingaben
        assert len(stufenzeiten) == len(laststufen), f"Stufenzeiten und Laststufen müssen für {tagestyp} gleich lang sein"
        assert sorted(stufenzeiten) == stufenzeiten, f"Zeitstufen müssen für {tagestyp} aufsteigend sortiert sein"
        
        load = np.zeros_like(time)
        
        # Stufenweiser Anstieg
        for i, t in enumerate(time):
            stufe_idx = sum(t >= np.array(stufenzeiten)) - 1
            stufe_idx = max(0, stufe_idx)
            
            if stufe_idx < len(laststufen) - 1:
                t1 = stufenzeiten[stufe_idx]
                t2 = stufenzeiten[stufe_idx + 1]
                load[i] = np.interp(t, [t1, t2], [laststufen[stufe_idx], laststufen[stufe_idx + 1]])
            else:
                # Letzte Stufe mit exponentiellem Abfall
                peak_time = stufenzeiten[-1]
                load[i] = laststufen[-1] * np.exp(-decay_rate * (t - peak_time))
        
        # Glätte die Last mit einer Gauß-Filterung
        load = gaussian_filter1d(load, sigma=smoothing_sigma)
        
        # Normiere die Last, sodass jeder 15-Minuten-Wert auf 1 normiert ist
        load /= np.sum(load)

                
        # Spalte für den aktuellen Tagestyp hinzufügen
        df[tagestyp] = load

    df.index = pd.to_datetime(df.index).strftime('%H:%M:%S')
    
    return df

# Lastprofil auf Monatliche Werte erweitern
def auf_monate_erweitern(df, seasonal_factors=None):
    """
    Erweitert die Spalten des DataFrames auf monatliche Profile, beeinflusst die Werte mit saisonalen Faktoren
    und glättet die resultierenden Profile.

    :param df: DataFrame mit E-Mobilitätslastprofilen (z. B. WT, SA, FT).
    :param seasonal_factors: Dictionary mit monatlichen Faktoren für jede Spalte im Format:
                             {'WT': [1.0, 0.9, ..., 1.1], 'SA': [...], 'FT': [...]}
                             Falls None, wird ein 1.0 verwendet.
    :return: Ein DataFrame mit geglätteten monatlichen Spalten (z. B. 01_WT, 02_SA, ...).
    """
    if seasonal_factors is None:
        # Standard-Saisonfaktoren (z. B. höhere Last im Winter, niedrigere im Sommer)
        seasonal_factors = {
            col: [1.0] * 12 for col in df.columns
        }

    # Sicherstellen, dass alle Spalten saisonale Faktoren haben
    for col in df.columns:
        if col not in seasonal_factors:
            raise ValueError(f"Keine saisonalen Faktoren für Spalte '{col}' gefunden.")

    # Erstelle neuen DataFrame mit monatlichen Spalten
    monthly_df = pd.DataFrame(index=df.index)

    for col in df.columns:
        for month, factor in enumerate(seasonal_factors[col], start=1):
            # Neue Spalte für jeden Monat erstellen
            monthly_col_name = f"{month:02d}_{col}"
            monthly_df[monthly_col_name] = df[col] * factor


    # Sortiere die Spalten nach Monaten
    monthly_df = monthly_df.reindex(sorted(monthly_df.columns, key=lambda x: int(x.split('_')[0])), axis=1)

    

    return monthly_df


def saisonale_schwankungen_modellieren(spalten=None):
    """
    Glättet die saisonalen Schwankungen basierend auf den monatlichen Anteilen, die in Summe 1 ergeben.
    Die Spalten WT, SA und FT werden separat betrachtet.

    :param spalten: Dictionary mit monatlichen Anteilen für jede Spalte im Format:
                    {'WT': [0.1, 0.1, ..., 0.1], 'SA': [...], 'FT': [...]}
                    Die Werte jeder Spalte müssen in Summe 1 ergeben.
    :return: Dictionary mit geglätteten monatlichen Faktoren für jede Spalte.
    """
    if spalten is None:
        raise ValueError("Es müssen monatliche Anteile für jede Spalte übergeben werden.")

    # Validierung der Eingaben
    for spalte, anteile in spalten.items():
        if not np.isclose(sum(anteile), 1.0):
            raise ValueError(f"Die monatlichen Anteile für '{spalte}' müssen in Summe 1 ergeben.")
        if len(anteile) != 12:
            raise ValueError(f"Die monatlichen Anteile für '{spalte}' müssen genau 12 Werte enthalten.")

    # Glättung der monatlichen Anteile
    geglättete_faktoren = {}
    for spalte, anteile in spalten.items():
        # Wiederhole die Werte zyklisch, um Übergänge zwischen Dezember und Januar zu glätten
        zyklische_anteile = np.concatenate(([anteile[-1]], anteile, [anteile[0]]))
        
        # Glätte die Werte mit einem Gauß-Filter
        geglättet = gaussian_filter1d(zyklische_anteile, sigma=1.0)
        
        # Entferne die zusätzlichen Werte und normiere die geglätteten Anteile
        geglättet = geglättet[1:-1]
        geglättet /= np.sum(geglättet)  # Normierung, damit die Summe wieder 1 ergibt
        
        geglättete_faktoren[spalte] = geglättet.tolist()

    return geglättete_faktoren


# Aufruf der Funktion

df_Lastprofil_EMob_tag = generiere_stufenfunktion( {'WT': ([0,2,4,6,8,10,12,14,16,18,20,22], [0.15,0.08,0.07,0.15,0.15,0.20,0.13,0.13,0.25,0.3,0.25,0.15]), 'SA': ([0,2,4,6,8,10,12,14,16,18,20,22], [0.15,0.1,0.08,0.2,0.25,0.2,0.18,0.18,0.25,0.28,0.2,0.15]), 'FT': ([0,2,4,6,8,10,12,14,16,18,20,22], [0.15,0.1,0.08,0.2,0.25,0.2,0.18,0.18,0.25,0.28,0.2,0.15])}, decay_rate = 0.0)
#df_Lastprofil_WP_tag = generiere_stufenfunktion( {'WT': ([5,8, 12, 19], [1, 1, 1, 1]), 'SA': ([7, 14, 20], [1, 1, 1]), 'FT': ([1, 12, 18], [1, 1, 1])}, decay_rate = 0.0)

#monatliche_faktoren_WP = {'WT':[0.196,0.171,0.138,0.059,0.027,0.006,0.0,0.0,0.016,0.067,0.13,0.19], 'SA': [0.196,0.171,0.138,0.059,0.027,0.006,0.0,0.0,0.016,0.067,0.13,0.19], 'FT':[0.196,0.171,0.138,0.059,0.027,0.006,0.0,0.0,0.016,0.067,0.13,0.19]}

df_Lastprofil_EMob_jahr = auf_monate_erweitern(df_Lastprofil_EMob_tag,)
#df_Lastprofil_WP_jahr = auf_monate_erweitern(df_Lastprofil_WP_tag, monatliche_faktoren_WP)

df_Lastprofil_EMob_jahr.to_excel(r'data\a_Eingangsdaten\Mobilität\EMob_Lastprofile_15min.xlsx', index=True)


#Erstellt einen df mit einer 15min Zeitreihe für ein Jahr und fügt die Lastprofile je nach Tagestyp ein
def erstelle_jahreszeitreihe(df_lastprofile):
    date_range = pd.date_range(start="2023-01-01 00:00", end="2023-12-31 23:45", freq="15T")
    df_jahr = pd.DataFrame({'timestamp': date_range}).set_index('timestamp')
    df_jahr['Zeitreihe'] = 0.0

    for timestamp in df_jahr.index:
        monat = timestamp.month
        tag = timestamp.day
        stunde_minute = timestamp.strftime('%H:%M:%S')

        # Bestimme den Tagestyp
        if timestamp.weekday() < 5:  # Montag bis Freitag
            tagestyp = 'WT'
        elif timestamp.weekday() == 5:  # Samstag
            tagestyp = 'SA'
        else:  # Sonntag
            tagestyp = 'FT'

        spaltenname = f"{monat:02d}_{tagestyp}"

        if spaltenname in df_lastprofile.columns and stunde_minute in df_lastprofile.index:
            df_jahr.at[timestamp, 'Zeitreihe'] = df_lastprofile.at[stunde_minute, spaltenname]
        else:
            raise ValueError(f"Spalte '{spaltenname}' oder Zeit '{stunde_minute}' nicht im Lastprofil DataFrame gefunden.")

    return df_jahr

df_jahr = erstelle_jahreszeitreihe(df_Lastprofil_EMob_jahr)


df_jahr['EEV_aufgeteilt'] = df_jahr['Zeitreihe'] * 261.05*1e3/365  # Annahme: 261,05 TWh/Jahr E-Mobilität in Deutschland --> in GWh umrechnen/365 Tage
df_jahr['Last_emob'] = df_jahr['EEV_aufgeteilt']*4  # Umrechnung von 15min Energiewerten auf Leistung in GW (4*15min = 1h)


df_jahr.to_excel(r'data\a_Eingangsdaten\Mobilität\EMob_Zeitreihe_15min_Jahr.xlsx', index=True)

e_mob_bedarf = df_jahr['Last_emob']

# Plot Linie: Datum vsE_mobbedarf (design angelehnt an x_plot_bubble_chart_2.py)
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Daten für das Plot vorbereiten
df_plot = df_jahr.copy()
df_plot.index = pd.to_datetime(df_plot.index)

#Ausschnitt einer Woche für das Plotten
df_plot = df_plot['2023-08-04':'2023-08-05']

fig, ax = plt.subplots(figsize=(12, 6))

plot_color = '#001450'  # gewünschter Farbcode für Linie und Beschriftungen
text_color = plot_color

# Linie mit kleinen Markern (keine Füllung)
ax.plot(
    df_plot.index,
    df_plot['Last_emob'],
    color=plot_color,
    linewidth=2,
    marker='o',
    markersize=4,
    alpha=0.95,
    label='E-Mobilitätsbedarf [GW]'
)

# Hintergrund weiß
ax.set_facecolor('white')
fig.patch.set_facecolor('white')

# Nur horizontale Gitternetzlinien
ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
ax.grid(False, axis='x')  # sicherstellen, dass keine vertikalen Gitternetzlinien gezeichnet werden

# Styling (ähnlich wie x_plot_bubble_chart_2.py) — Farben auf #001450 setzen
ax.set_title('modellierter E-Mobilitätsbedarf 2023', fontsize=14, fontweight='bold', color=text_color)
ax.set_xlabel('Datum', fontsize=12, color=text_color)
ax.set_ylabel('E-Mobilitätsbedarf [GW]', fontsize=12, color=text_color)

# Y-Achse bei 0 beginnen lassen
ax.set_ylim(bottom=0)

# Datumsformatierung: Stunden auf der x-Achse (ein Tick pro Stunde)
ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
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
plt.savefig(r'data\a_Eingangsdaten\Mobilität\E_Mob_Woche_plot.png', dpi=150)
plt.close(fig)

print('Ende x_emob.py')

# %%
