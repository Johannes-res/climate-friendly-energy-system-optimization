import pandas as pd
#Bedarfe laden
import sys
from pathlib import Path
    # ensure the parent of 'scripts_opt_neu' (project root) is on sys.path so imports like
    # 'scripts_opt_neu.a_Eingangsdaten...' can be resolved
    # sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    # from scripts_opt_neu.a_Eingangsdaten.x_Bedarfe_gesamt import strom_bedarf_gesamt
strom_bedarf_gesamt = pd.read_excel(r'data\b_Optimierung\Bedarfe_Gesamt_mit_Indu_15min_2023.xlsx', index_col=0)
täglicher_Bedarf_gesamt = pd.read_excel(r'data\b_Optimierung\tägliche_Bedarfe_Gesamt_2023.xlsx', index_col=0)

#Verfügbarkeitsfaktoren für Stromerzeuger laden
        #from scripts_opt_neu.a_Eingangsdaten.y_verfügbarkeiten_strom import strom_verfügbarkeiten_23
strom_verfügbarkeiten_23 = pd.read_excel(r'data\b_Optimierung\Verfügbarkeiten_Stromerzeuger_15min_2023.xlsx', index_col=0)
solarthermie_verfügbarkeiten_23 = pd.read_excel(r'data\b_Optimierung\Verfügbarkeiten_Solarthermie_täglich_2023.xlsx', index_col=0)
solarthermie_verfügbarkeiten_23.index = pd.to_datetime(solarthermie_verfügbarkeiten_23.index).date  # Nur Datum, keine Uhrzeit
# allg. Parameter/Variablen laden
    #df_parameter = pd.read_excel(r'data\a_Eingangsdaten\Optimierungsgrößen - ohne Speicher.xlsx', index_col=0) # ohne speicher
df_parameter = pd.read_excel(r'data\a_Eingangsdaten\Optimierungsgrößen - Strom und Wärme_Wandler_experimentell.xlsx', index_col=0)

# Hilfslisten (werden hier erzeugt, ggf. Exporte falls nötig)
technologien = df_parameter.index.tolist()
traeger_dict = df_parameter['Energieträger'].to_dict()
energietraeger = list(dict.fromkeys(traeger_dict.values()))
art_dict = df_parameter['Art'].to_dict()
technologieart = list(dict.fromkeys(art_dict.values()))
kosten = (df_parameter['Kosten [Mio.€/GW]']*1000).to_dict()  # Umrechnung in €/MW
wirkungsgrade = (df_parameter['Wirkungsgrad']).to_dict()
    #untere_kapazitaetsgrenzen = (df_parameter['untere Kapagrenze [MWh]']).to_dict()
    #obere_kapazitaetsgrenzen = (df_parameter['obere Kapagrenze [MWh]']).to_dict()
    #selbstentladungsrate = (df_parameter['Selbstentladungsrate [%/Tag]']).to_dict()
c_rate = (df_parameter['C-Rate']).to_dict()
lebensdauer = (df_parameter['Lebensdauer']).to_dict()

#für Wandler Input aufnehmen
input_wandler = (df_parameter['Input']).to_dict()

# Filter für gemeinsame Technologien in Erzeuger-Verfügbarkeits-Daten
gemeinsame_s_techs = [t for t in strom_verfügbarkeiten_23.columns if t in df_parameter.index and traeger_dict[t] == 'Strom']
strom_verfügbarkeiten_23 = strom_verfügbarkeiten_23[gemeinsame_s_techs]

    #gemeinsame_wae_techs = [t for t in df_erzeuger_waerme.columns if t in df_parameter.index and traeger_dict[t] == 'Wärme']
    #df_erzeuger_waerme = df_erzeuger_waerme[gemeinsame_wae_techs]

df_bedarf = strom_bedarf_gesamt.copy()
df_bedarf_daily = täglicher_Bedarf_gesamt.copy()
df_bedarf_daily.index = pd.to_datetime(df_bedarf_daily.index).date  # Nur Datum, keine Uhrzeit

print('Ende inputs.py')