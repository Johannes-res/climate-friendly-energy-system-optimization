from x_strombedarf_org import strom_last_23
from x_emobbedarf import e_mob_bedarf

#Gesamtbedarf berechnen
bedarf_gesamt = strom_last_23.copy()
bedarf_gesamt['E_Mob_Bedarf [MW]'] = e_mob_bedarf
bedarf_gesamt['Strom_Gesamt_Bedarf [MW]'] = bedarf_gesamt['Strom_Last [MW]'] + bedarf_gesamt['E_Mob_Bedarf [MW]']+ bedarf_gesamt['Industrie_Strom_Last [MW]']


bedarf_gesamt.to_excel(r'data\b_Optimierung\Bedarfe_Gesamt_mit_Indu_15min_2023.xlsx', index=True)

print('Ende x_Bedarfe_gesamt.py')