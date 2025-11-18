import pandas as pd



df_bedarf_org = pd.read_excel(r'data\Ausgabe\Bedarf_22_klimaneutral.xlsx')
df_erzeuger_strom = pd.read_excel(r'data\energy-charts\energy-charts_Öffentliche_Nettostromerzeugung_in_Deutschland_2022.xlsx')
df_erzeuger_wärme = pd.read_excel(r'data\Ausgabe\erzeugung_waerme_22.xlsx')
df_erzeuger_strom.index = pd.to_datetime(df_erzeuger_strom.iloc[:, 0], format='%Y-%m-%d %H:%M:%S')
df_erzeuger_wärme.index = pd.to_datetime(df_erzeuger_wärme.iloc[:, 0], format='%Y-%m-%d %H:%M:%S')
# Erzeugerzeitreihe aufbereiten
df_bedarf = pd.DataFrame({
    'Strom': df_bedarf_org['Last_prognose [MWh]'].values * 4,
    'Wasserstoff': df_bedarf_org['Wasserstoff'].values * 4,
    'Wärme': df_bedarf_org['Wärmepumpen'].values * 4 + df_bedarf_org['Thermie'].values*4,
    'E-Fuel': df_bedarf_org['E-Fuels'].values * 4,
    'Biomasse': df_bedarf_org['Biomasse'].values * 4
}, index=pd.to_datetime(df_bedarf_org['Datum (UTC)']))


# Begrenze die DataFrames auf eine bestimmte Woche (z.B. Kalenderwoche 10)
# Annahme: df_bedarf hat eine Spalte 'Datum' oder einen DatetimeIndex
start_date = '2022-03-07 00:00:00'  # Beispiel: Montag der gewünschten Woche
end_date = '2022-03-13 00:00:00'    # Beispiel: Sonntag der gewünschten Woche

# start_date = '2022-05-01 00:00:00'  # Beispiel: Montag der gewünschten Woche
# end_date = '2022-05-31 23:45:00'    # Beispiel: Sonntag der gewünschten Woche

def begrenze_auf_zeitraum(df, start_date, end_date):
    """
    Begrenze DataFrame auf den Zeitraum zwischen start_date und end_date (inklusive).
    Annahme: Das Datum befindet sich im Index und ist vom Typ DatetimeIndex.
    """
    df = df.copy()
    df.index = pd.to_datetime(df.index)  # Sicherstellen, dass der Index ein DatetimeIndex ist])
    return df.loc[(df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))]

df_bedarf = begrenze_auf_zeitraum(df_bedarf, start_date, end_date)
df_erzeuger_strom = begrenze_auf_zeitraum(df_erzeuger_strom, start_date, end_date)
df_erzeuger_wärme = begrenze_auf_zeitraum(df_erzeuger_wärme, start_date, end_date)

# Sicherstellen, dass keine NaN-Werte in den relevanten DataFrames vorhanden sind
df_bedarf = df_bedarf.fillna(0)
df_erzeuger_strom = df_erzeuger_strom.fillna(0)
df_erzeuger_wärme = df_erzeuger_wärme.fillna(0)

# Gemeinsame Zeitbasis für alle DataFrames
common_index = df_bedarf.index.intersection(df_erzeuger_strom.index).intersection(df_erzeuger_wärme.index)
df_bedarf = df_bedarf.loc[common_index]
df_erzeuger_strom = df_erzeuger_strom.loc[common_index]
df_erzeuger_wärme = df_erzeuger_wärme.loc[common_index]

# Normieren der Werte aus df_erzeuger_strom auf deren Maximalwerte (ohne die Datetime-Spalte)
datetime_col = df_erzeuger_strom.columns[0]
df_erzeuger_strom = df_erzeuger_strom.drop(columns=[datetime_col])
df_erzeuger_strom = df_erzeuger_strom.drop(columns=['Pumpspeicher'], errors='ignore')  # 'Pumpspeicher' entfernen, falls vorhanden
df_erzeuger_strom[df_erzeuger_strom.columns] = df_erzeuger_strom / df_erzeuger_strom.abs().max()

df_erzeuger_strom['Wind_Onshore'] = df_erzeuger_strom['Wind Onshore']
df_erzeuger_strom['Wind_Offshore'] = df_erzeuger_strom['Wind Offshore']

print("Daten erfolgreich eingelesen und aufbereitet.")