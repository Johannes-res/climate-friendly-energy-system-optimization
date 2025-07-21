import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def generate_emobility_load(profiles: dict = {'WT': ([5, 12, 19], [0.2, 0.6, 1.0]), 'SA': ([6, 14, 20], [0.1, 0.5, 0.8])}):
    """
    Generiert mehrere stufenweise E-Mobilitätslastprofile als DataFrame mit Zeitindex.
    
    :param profiles: Ein Dictionary, bei dem die Schlüssel die Tagestypen sind (z. B. 'WT', 'SA') 
                     und die Werte Listen mit Stufenzeiten und Laststufen.
    :return: Ein DataFrame mit Zeitindex und einer Spalte pro Tagestyp.
    """
    # Zeitachse in 15-Minuten-Intervallen
    time = np.arange(0, 24.25, 0.25)
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
                decay_rate = 0.4
                peak_time = stufenzeiten[-1]
                load[i] = laststufen[-1] * np.exp(-decay_rate * (t - peak_time))
        
        # Spalte für den aktuellen Tagestyp hinzufügen
        df[tagestyp] = load

    df.index = pd.to_datetime(df.index).strftime('%H:%M')
    
    return df

df_Lastprofil_EMob = generate_emobility_load( {'WT': ([5,8, 12, 19], [0.2, 0.5, 0.6, 1.0]), 'SA': ([7, 14, 20], [0.3, 0.5, 0.8])})
for column in df_Lastprofil_EMob.columns:
    print(f"Summe der Einzelwerte für {column}: {df_Lastprofil_EMob[column].sum()}")
print('23r')

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

plot_custom_load(df_Lastprofil_EMob)
print("E-Mobilitätslastprofile erfolgreich generiert und dargestellt.")
