from datetime import datetime
import pandas as pd
import numpy as np

df_tavg =pd.read_excel(r'data\Wetterdaten\durchschnitt_täglich_2023.xlsx', index_col=0)

# Zeitraum definieren
start = datetime(2023, 1, 1)
end = datetime(2023, 12, 31)

# Warmwasserbedarf für das Jahr 2023 in GWh (Beispielwert, bitte anpassen)
WWB_a = 80.7e3  # WWB_Gebäude 2023 in GWh

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
df_wwb = pd.DataFrame({'Warmwasserbedarf [GWh]': daily_values_gwh}, index=dates)


# Ergebnis in eine Excel-Datei speichern
df_wwb.to_excel(r'data\a_Eingangsdaten\Wärme\Warmwasserbedarf_täglich_23.xlsx')

def bedarf_mit_strom_decken(df,df_tavg):
    """
    Berechnet den Strombedarf zur Deckung des Warmwasserbedarfs mit Wärmepumpen.
    cop_wärmepumpe: Coefficient of Performance der Wärmepumpe
    
    Rückgabe: DataFrame mit zusätzlicher Spalte 'Strombedarf_Warmwasser [GW]'
    """
    df = df.copy()
    df_tavg = df_tavg.copy()
    df_tavg.index = pd.to_datetime(df_tavg.index)
    cop_wärmepumpe = 0.075*(df_tavg['tavg']+15)+2  # COP-Berechnung basierend auf Außentemperatur und einer Funktion, welche den COP-Wert aus den Korrelationsfaktoren mittelt
    cop_wärmepumpe.index = cop_wärmepumpe.index.normalize()
    df['Last_Warmwasser [GW]'] = df['Warmwasserbedarf [GWh]'] / 24  # Umrechnung in GW (da tägliche Werte)
    df['Strombedarf_Warmwasser [GW]'] = df['Last_Warmwasser [GW]'] / cop_wärmepumpe.reindex(df.index).values
    return df



def expand_daily_to_15min(df_daily, smooth_transitions=True, transition_steps=4, add_peaks=True, peak_factor=1.15):
    """
    Erweitert ein tägliches DataFrame zu einer 15-Minuten-Zeitreihe.
    Verarbeitet alle Spalten im DataFrame:
    - 'Warmwasserbedarf [GWh]': Wird gleichmäßig auf 96 Intervalle verteilt
    - 'Last_Warmwasser [GW]': Wird mit Peaks und Glättung versehen
    - 'Strombedarf_Warmwasser [GW]': Wird mit Peaks und Glättung versehen
    
    Parameter:
    ----------
    df_daily : pd.DataFrame
        Tägliche Werte mit datetime-Index
    smooth_transitions : bool
        Falls True, werden Tagesübergänge geglättet
    transition_steps : int
        Anzahl der 15-min-Schritte für die Glättung (Standard: 4 = 1 Stunde)
    add_peaks : bool
        Falls True, werden gleitende Morgen- und Abendspitzen hinzugefügt
    peak_factor : float
        Erhöhungsfaktor für Spitzenzeiten (1.15 = +15%)
        
    Rückgabe: 
    ---------
    pd.DataFrame mit 15-min Index und allen drei Spalten
    """
    import numpy as np
    
    df_daily = df_daily.copy()
    df_daily.index = pd.to_datetime(df_daily.index)

    # 15-Minuten-Index vom ersten bis zum letzten Tag (inklusive letzter Tag 23:45)
    start = df_daily.index.min()
    end = df_daily.index.max() + pd.Timedelta(days=1) - pd.Timedelta(minutes=15)
    idx_15 = pd.date_range(start=start, end=end, freq='15T')

    # Ergebnis-DataFrame vorbereiten
    df_result = pd.DataFrame(index=idx_15)
    
    # ✅ Verarbeite jede Spalte einzeln
    for value_col in df_daily.columns:
        
        # ✅ SCHRITT 1: Umrechnung in tägliche Energie [GWh]
        if '[GW]' in value_col:
            # Input ist Leistung [GW] → in Energie [GWh] umrechnen
            tägliche_energie = df_daily[value_col] * 24  # GW × 24h = GWh
            output_col_name = value_col  # Behalte Original-Namen für Output
        else:
            # Input ist bereits Energie [GWh]
            tägliche_energie = df_daily[value_col]
            output_col_name = value_col.replace('[GWh]', '[GW]')
        
        # Index normalisieren
        tägliche_energie.index = tägliche_energie.index.normalize()
        
        # ✅ SCHRITT 2: Auf 15-min verteilen (96 Intervalle pro Tag)
        day_index_for_15 = idx_15.normalize()
        energie_15min = tägliche_energie.reindex(day_index_for_15).values / 96.0  # GWh pro 15min
        
        series_energie = pd.Series(data=energie_15min, index=idx_15, name='Energie_15min [GWh]')
        
        # ✅ SCHRITT 3: Morgen-/Abendspitzen hinzufügen (nur bei Leistungsspalten)
        if add_peaks and '[GW]' in value_col:
            series_energie = add_smooth_energy_peaks(series_energie, tägliche_energie, peak_factor)
        
        # ✅ SCHRITT 4: Tagesübergänge glätten (nur bei Leistungsspalten)
        if smooth_transitions and '[GW]' in value_col and len(tägliche_energie) > 1:
            series_energie = smooth_energy_transitions(series_energie, tägliche_energie, transition_steps)
        
        # ✅ SCHRITT 5: Umrechnung in Leistung [GW]
        # Energie [GWh] / Zeitintervall [h] = Leistung [GW]
        # 15min = 0.25h → Leistung = Energie / 0.25
        leistung_15min = series_energie / 0.25
        
        # Spalte zum Ergebnis hinzufügen
        df_result[output_col_name] = leistung_15min.values
    
    return df_result


def add_smooth_energy_peaks(series_energie, tägliche_energie, peak_factor=1.15):
    """
    Fügt gleitende Morgen- (7 Uhr) und Abendspitzen (19 Uhr) mit Gaussian-Profil hinzu.
    Arbeitet mit ENERGIE [GWh], sodass die Tagesenergie automatisch erhalten bleibt.
    
    Parameter:
    ----------
    series_energie : pd.Series
        15-Minuten-Energiewerte [GWh pro 15min]
    tägliche_energie : pd.Series
        Tägliche Energie [GWh] (Index: normalisierte Datumswerte)
    peak_factor : float
        Maximaler Erhöhungsfaktor für Spitzenzeiten (1.15 = +15% am Peak)
        
    Rückgabe:
    ---------
    pd.Series mit gleitenden Spitzen (Tagesenergie bleibt erhalten)
    """
    import numpy as np
    
    series_peak = series_energie.copy()
    
    # Iteriere über alle Tage
    day_list = sorted(tägliche_energie.index)
    
    for day in day_list:
        # Alle 15-min-Zeitpunkte dieses Tages
        day_mask = series_energie.index.normalize() == day
        day_indices = series_energie.index[day_mask]
        
        if len(day_indices) == 0:
            continue
        
        # Tagesenergie [GWh]
        total_energy = tägliche_energie.loc[day]
        
        # Anzahl der 15-min-Intervalle (sollte 96 sein)
        n_steps = len(day_indices)
        
        # ✅ GAUSSIAN-PROFIL (zwei Peaks pro Tag)
        time_of_day = np.arange(n_steps)
        
        # Morgenspitze: Gaussian-Peak zentriert bei 7 Uhr (Index 28)
        morning_center = 28  # 7:00 Uhr = 28 × 15min
        morning_width = 8    # Breite: ±2 Stunden
        morning_peak = np.exp(-0.5 * ((time_of_day - morning_center) / morning_width) ** 2)
        
        # Abendspitze: Gaussian-Peak zentriert bei 19 Uhr (Index 76)
        evening_center = 76  # 19:00 Uhr = 76 × 15min (für Warmwasser später als Raumwärme)
        evening_width = 8    # Breite: ±2 Stunden
        evening_peak = np.exp(-0.5 * ((time_of_day - evening_center) / evening_width) ** 2)
        
        # Kombiniertes Profil (beide Peaks addieren)
        combined_peak = morning_peak + evening_peak
        
        # Normieren auf Bereich [1.0, peak_factor]
        peak_profile = 1.0 + (peak_factor - 1.0) * (combined_peak / combined_peak.max())
        
        # ✅ Energie pro 15-min-Intervall [GWh]
        base_energy_per_interval = total_energy / 96.0
        energy_with_peaks = base_energy_per_interval * peak_profile
        
        # ✅ Normierung: Skaliere so, dass Summe = total_energy
        actual_sum = np.sum(energy_with_peaks)
        if actual_sum > 0:
            energy_with_peaks *= (total_energy / actual_sum)
        
        # Werte setzen
        series_peak.loc[day_mask] = energy_with_peaks
    
    return series_peak


def smooth_energy_transitions(series_energie, tägliche_energie, transition_steps=4):
    """
    Glättet Energiesprünge an Tagesübergängen durch lineare Interpolation.
    Arbeitet mit ENERGIE [GWh], sodass die Gesamtenergie erhalten bleibt.
    
    Parameter:
    ----------
    series_energie : pd.Series
        15-Minuten-Energiewerte [GWh pro 15min]
    tägliche_energie : pd.Series
        Tägliche Energie [GWh] (Index: normalisierte Datumswerte)
    transition_steps : int
        Anzahl der 15-min-Schritte für die Glättung (4 = 1 Stunde)
        
    Rückgabe:
    ---------
    pd.Series mit geglätteten Übergängen (Gesamtenergie erhalten)
    """
    import numpy as np
    
    series_smooth = series_energie.copy()
    
    # Iteriere über alle Tagesübergänge
    day_list = sorted(tägliche_energie.index)
    
    for i in range(len(day_list) - 1):
        current_day = day_list[i]
        next_day = day_list[i + 1]
        
        # Zeitpunkt des Übergangs (Mitternacht)
        transition_time = next_day
        
        # Indizes für Glättung: transition_steps VOR und NACH Mitternacht
        try:
            transition_idx = series_energie.index.get_loc(transition_time)
        except KeyError:
            continue
        
        # Sicherstellen, dass genug Datenpunkte vorhanden sind
        start_idx = max(0, transition_idx - transition_steps)
        end_idx = min(len(series_energie), transition_idx + transition_steps)
        
        n_total = end_idx - start_idx
        
        if n_total == 0:
            continue
        
        # Original-Energiewerte im Übergangsbereich [GWh]
        original_energies = series_smooth.iloc[start_idx:end_idx].values.copy()
        
        # ✅ Lineare Interpolation zwischen erstem und letztem Wert
        start_value = original_energies[0]
        end_value = original_energies[-1]
        interpolated_energies = np.linspace(start_value, end_value, n_total)
        
        # ✅ Energieerhaltung: Original-Gesamtenergie im Übergangsbereich
        original_total = np.sum(original_energies)
        interpolated_total = np.sum(interpolated_energies)
        
        # Korrekturfaktor, um Original-Energie zu erhalten
        if interpolated_total > 0:
            correction_factor = original_total / interpolated_total
            interpolated_energies *= correction_factor
        
        # Werte ersetzen
        series_smooth.iloc[start_idx:end_idx] = interpolated_energies
    
    return series_smooth



df_strom = bedarf_mit_strom_decken(df_wwb, df_tavg)

# ✅ Alle drei Spalten werden verarbeitet
df_15min = expand_daily_to_15min(
    df_strom, 
    smooth_transitions=False, 
    transition_steps=4, 
    add_peaks=False, 
    peak_factor=1.15
)
df_15min.drop(columns=["Warmwasserbedarf [GW]"], inplace=True)  # Diese Spalte wird nicht benötigt
df_15min.to_excel(r'data\a_Eingangsdaten\Wärme\Warmwasser_Strombedarf_15min_23.xlsx')



print("✓ Warmwasser-Daten (15min) gespeichert:")
print(f"  - Spalten: {list(df_15min.columns)}")
print(f"  - Zeitraum: {df_15min.index.min()} bis {df_15min.index.max()}")
print(f"  - Anzahl Zeitpunkte: {len(df_15min)}")


# ========================================
# VISUALISIERUNGEN
# ========================================

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plot_color = '#001450'
text_color = plot_color

# ========================================
# 1. JAHRESANSICHT (Tägliche Werte) - BEIDE SPALTEN
# ========================================

# Tageswerte aus 15-min-Daten aggregieren
df_plot_year = df_15min.resample('1D').mean()
df_plot_year.index = pd.to_datetime(df_plot_year.index)

fig, ax = plt.subplots(figsize=(14, 6))

# Beide Spalten plotten
ax.plot(
    df_plot_year.index,
    df_plot_year['Last_Warmwasser [GW]'],
    color='#001450',  # Dunkelblau für thermische Last
    linewidth=2,
    marker=None,
    alpha=0.95,
    label='Last Warmwasser (thermisch)'
)

ax.plot(
    df_plot_year.index,
    df_plot_year['Strombedarf_Warmwasser [GW]'],
    color='#e74c3c',  # Rot für Strom
    linewidth=2,
    marker=None,
    alpha=0.95,
    label='Strombedarf (elektrisch, mit WP-COP)'
)

# Styling
ax.set_facecolor('white')
fig.patch.set_facecolor('white')
ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
ax.grid(False, axis='x')

ax.set_title('Warmwasserbedarf 2023 - Jahresübersicht', fontsize=14, fontweight='bold', color=text_color)
ax.set_xlabel('Monat', fontsize=12, color=text_color)
ax.set_ylabel('Leistung [GW]', fontsize=12, color=text_color)

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
plt.savefig(r'data\a_Eingangsdaten\Wärme\Warmwasserbedarf_Jahresansicht_2023.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("✓ Jahresansicht gespeichert: Warmwasserbedarf_Jahresansicht_2023.png")


# ========================================
# 2. WOCHENANSICHT (15-min-Werte) - BEIDE SPALTEN
# ========================================

week_start = pd.Timestamp('2023-01-09')
week_end = week_start + pd.Timedelta(days=7) - pd.Timedelta(minutes=15)

df_week = df_15min[(df_15min.index >= week_start) & (df_15min.index <= week_end)]

fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(
    df_week.index,
    df_week['Last_Warmwasser [GW]'],
    color='#001450',
    linewidth=2,
    alpha=0.95,
    label='Last Warmwasser (thermisch)'
)

ax.plot(
    df_week.index,
    df_week['Strombedarf_Warmwasser [GW]'],
    color='#e74c3c',
    linewidth=2,
    alpha=0.95,
    label='Strombedarf (elektrisch, mit WP-COP)'
)

# Styling
ax.set_facecolor('white')
fig.patch.set_facecolor('white')
ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
ax.grid(which='major', axis='x', color='#e6e6e6', linewidth=0.5, alpha=0.5)

ax.set_title(f'Warmwasserbedarf - Wochenansicht ({week_start.strftime("%d.%m.")} - {week_end.strftime("%d.%m.%Y")})', 
             fontsize=14, fontweight='bold', color=text_color)
ax.set_xlabel('Datum', fontsize=12, color=text_color)
ax.set_ylabel('Leistung [GW]', fontsize=12, color=text_color)

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
plt.savefig(r'data\a_Eingangsdaten\Wärme\Warmwasserbedarf_Wochenansicht_2023.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("✓ Wochenansicht gespeichert: Warmwasserbedarf_Wochenansicht_2023.png")


# ========================================
# 3. TAGESANSICHT (15-Minuten-Werte) - BEIDE SPALTEN
# ========================================

day_start = pd.Timestamp('2023-01-15')
day_end = day_start + pd.Timedelta(days=1) - pd.Timedelta(minutes=15)

df_day = df_15min[(df_15min.index >= day_start) & (df_15min.index <= day_end)]

fig, ax = plt.subplots(figsize=(14, 6))

ax.plot(
    df_day.index,
    df_day['Last_Warmwasser [GW]'],
    color='#001450',
    linewidth=2,
    alpha=0.95,
    label='Last Warmwasser (thermisch)'
)

ax.plot(
    df_day.index,
    df_day['Strombedarf_Warmwasser [GW]'],
    color='#e74c3c',
    linewidth=2,
    alpha=0.95,
    label='Strombedarf (elektrisch, mit WP-COP)'
)

# Styling
ax.set_facecolor('white')
fig.patch.set_facecolor('white')
ax.grid(which='major', axis='y', color='#e6e6e6', linewidth=0.8)
ax.grid(which='major', axis='x', color='#e6e6e6', linewidth=0.5, alpha=0.5)

ax.set_title(f'Warmwasserbedarf - Tagesansicht ({day_start.strftime("%d.%m.%Y")})', 
             fontsize=14, fontweight='bold', color=text_color)
ax.set_xlabel('Uhrzeit', fontsize=12, color=text_color)
ax.set_ylabel('Leistung [GW]', fontsize=12, color=text_color)

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
plt.savefig(r'data\a_Eingangsdaten\Wärme\Warmwasserbedarf_Tagesansicht_2023.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print("✓ Tagesansicht gespeichert: Warmwasserbedarf_Tagesansicht_2023.png")

print("\n✓ Alle 3 Visualisierungen erfolgreich erstellt!")
print("  1. Jahresansicht (täglich, beide Spalten)")
print("  2. Wochenansicht (15-min, beide Spalten)")
print("  3. Tagesansicht (15-min, beide Spalten)")


print('Warmwasserbedarf skript beendet')