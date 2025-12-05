import pandas as pd
from x_strombedarf_org import strom_last_23
print("✓ strom_last_23 importiert")

from x_emobbedarf import e_mob_bedarf
from x_raumwärmebedarf import rwb
from x_warmwasserbedarf import wwb
#Gesamtstrombedarf berechnen
strom_bedarf_gesamt = strom_last_23.copy()
strom_bedarf_gesamt['E_Mob_Bedarf [MW]'] = e_mob_bedarf
strom_bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'] = strom_bedarf_gesamt['Strom_Last [MW]'] + strom_bedarf_gesamt['E_Mob_Bedarf [MW]']+ strom_bedarf_gesamt['Industrie_Strom_Last [MW]']

#Gesamtwärmebedarf berechnen
#Raumwärme und Warmasserbedarf kann zusammengefasst werden. Prozesswärme muss wenn dann spearat mit untersch. Temp niveaus betrachtet werden

täglicher_Bedarf_gesamt = rwb.copy()
täglicher_Bedarf_gesamt['Warmwasserbedarf [MWh]'] = wwb['Warmwasserbedarf [MWh]']


täglicher_Bedarf_gesamt = pd.concat([rwb, wwb], axis=1)
täglicher_Bedarf_gesamt['Warmwasserbedarf [GWh]'].drop 
täglicher_Bedarf_gesamt['Wärme_Gesamt_Bedarf [MWh]'] = täglicher_Bedarf_gesamt['Raumwärmebedarf [MWh]'] + täglicher_Bedarf_gesamt['Warmwasserbedarf [MWh]'] #zzgl niedertemp prozesswärme


täglicher_Bedarf_gesamt.to_excel(r'data\b_Optimierung\tägliche_Bedarfe_Gesamt_2023.xlsx', index=True)
strom_bedarf_gesamt.to_excel(r'data\b_Optimierung\Bedarfe_Gesamt_mit_Indu_15min_2023.xlsx', index=True)

print('Ende x_Bedarfe_gesamt.py')