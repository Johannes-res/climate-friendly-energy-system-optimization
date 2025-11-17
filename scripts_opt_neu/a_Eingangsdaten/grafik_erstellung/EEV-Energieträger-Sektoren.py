import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import matplotlib.patches as mpatches
import numpy as np



#excel datei mit werten laden
file_path = r'data\a_Eingangsdaten\Bedarf\Anwendungsbilanzen\Endenergieverbrauch nach Energieträgern und Sektoren im Jahr 2023.xlsx'
df_excel = pd.read_excel(file_path, sheet_name='Tabelle1')

# Daten aus Excel in das gewünschte Format bringen:
# - erste Spalte enthält die x-Kategorien (Sektoren)
# - die übrigen Spaltenköpfe sind die y-Kategorien (Energieträger)
# - Ergebnis: Liste `data` mit Einträgen [x_cat, y_cat, Wert]
df_excel = df_excel.copy()
sector_col = df_excel.columns[0]
x_from_excel = df_excel[sector_col].astype(str).tolist()
y_from_excel = list(df_excel.columns[1:])

data = []
for _, row in df_excel.iterrows():
    sector = str(row[sector_col])
    for carrier in y_from_excel:
        val = row[carrier]
        if pd.isna(val):
            continue
        try:
            num = float(val)
        except Exception:
            # falls der Wert nicht konvertierbar ist, überspringen
            continue
        data.append([sector, carrier, num])

# Kategorien (Reihenfolge aus den Daten übernehmen)
x_categories = list(dict.fromkeys([d[0] for d in data]))
y_categories = y_from_excel.copy()



# Kategorien und Werte definieren
#x_categories = ["Haushalte", "GHD", "Verkehr", "Industrie"]
#y_categories = ["Stein- und Braunkohle", "Mineralöle", "Gase",
#                "erneuerbare Energien", "Strom", "Fernwärme", "sonstige"]

# Beispielwerte: [x, y, größe]
""" data = [
    ["Haushalte", "Stein- und Braunkohle", 3.25],
    ["GHD", "Stein- und Braunkohle", 0.24],
    ["Verkehr", "Stein- und Braunkohle", 0],
    ["Industrie", "Stein- und Braunkohle", 92.37],

    ["Haushalte", "Mineralöle", 118.56],
    ["GHD", "Mineralöle", 49.2],
    ["Verkehr", "Mineralöle", 641.46],
    ["Industrie", "Mineralöle", 26.26],

    ["Haushalte", "Gase", 40],
    ["GHD", "Gase", 80],
    ["Verkehr", "Gase", 65],
    ["Industrie", "Gase", 30],

    ["Haushalte", "erneuerbare Energien", 40],
    ["GHD", "erneuerbare Energien", 80],
    ["Verkehr", "erneuerbare Energien", 65],
    ["Industrie", "erneuerbare Energien", 30],

    ["Haushalte", "Strom", 40],
    ["GHD", "Strom", 80],
    ["Verkehr", "Strom", 65],
    ["Industrie", "Strom", 30],

    ["Haushalte", "Fernwärme", 40],
    ["GHD", "Fernwärme", 80],
    ["Verkehr", "Fernwärme", 65],
    ["Industrie", "Fernwärme", 30],

    ["Haushalte", "sonstige", 40],
    ["GHD", "sonstige", 80],
    ["Verkehr", "sonstige", 65],
    ["Industrie", "sonstige", 30],
] """

# Farben für jede y-Kategorie definieren (rgb 0-1)
cd_palette = [
     # (0/255, 20/255, 80/255),
    (0/255, 0/255, 140/255),
    (47/255, 87/255, 178/255),
    (115/255, 105/255, 190/255),
    (188/255, 21/255, 137/255),
    (210/255, 15/255, 65/255),
    (200/255, 80/255, 0/255),
    (255/255, 199/255, 0/255),
    (118/255, 122/255, 35/255),
    (0/255, 125/255, 75/255),
    (10/255, 119/255, 127/255),
    (151/255, 198/255, 255/255),
    (200/255, 200/255, 255/255),
    (255/255, 185/255, 255/255),
    (255/255, 170/255, 165/255),
    (255/255, 190/255, 120/255),
    (255/255, 228/255, 131/255),
    (210/255, 220/255, 70/255),
    (140/255, 230/255, 170/255),
    (140/255, 230/255, 215/255)
]

# DataFrame erstellen
df = pd.DataFrame(data, columns=["x_cat", "y_cat", "Wert"])

# Kategorien codieren für Scatter-Plot
df['x_code'] = pd.Categorical(df['x_cat'], categories=x_categories, ordered=True).codes
df['y_code'] = pd.Categorical(df['y_cat'], categories=y_categories, ordered=True).codes

# Mapping y-Kategorie -> Farbe (nutzt die ersten len(y_categories) Farben)
color_map = {cat: cd_palette[i] for i, cat in enumerate(y_categories)}
df['color'] = df['y_cat'].map(color_map)

# Stil
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'opensans' # hier letzte Änderung!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Weniger breite Figur, Blasen enger zusammenziehen
fig, ax = plt.subplots(figsize=(9, 7), dpi=120)  # schmalere Breite als vorher

# gewünschte Linienfarbe (rgb 0-1)
line_color = (0/255, 20/255, 80/255)

# Kompressionsfaktor für x-Abstand (kleiner -> enger beieinander)
x_spacing = 0.6
df['x_pos'] = df['x_code'] * x_spacing
df['y_pos'] = df['y_code']  # y unverändert

# Bubble Chart: Farben pro y-Kategorie verwenden
size_scale = 4
df['s'] = df['Wert'] * size_scale
scatter = ax.scatter(
    df['x_pos'],
    df['y_pos'],
    s=df['s'],   # Skalierung der Blasengröße (points^2)
    color=df['color'],
    alpha=0.8,
    edgecolors=df['color'].tolist(),
    linewidths=0.5
)

# Achsenbeschriftungen, ticks an komprimierten Positionen
ticks_x = (np.arange(len(x_categories)) * x_spacing)
ax.set_xticks(ticks_x)
ax.set_xticklabels(x_categories, rotation=0, fontsize=11, fontweight='bold')
ax.xaxis.tick_top()
ax.xaxis.set_label_position('top')

ax.set_yticks(range(len(y_categories)))
ax.set_yticklabels(y_categories, fontsize=11, fontweight='bold')
ax.invert_yaxis()

# Achsen (Spines und Tick-Marker) ausblenden, aber Tick-Labels behalten
for spine in ax.spines.values():
    spine.set_visible(False)
ax.tick_params(axis='both', which='both', length=0)
ax.tick_params(colors=line_color, which='both')
ax.xaxis.label.set_color(line_color)
ax.yaxis.label.set_color(line_color)
ax.xaxis.label.set_fontweight('bold')
ax.yaxis.label.set_fontweight('bold')
ax.title.set_color(line_color)

for lbl in ax.get_xticklabels():
    lbl.set_fontweight('bold')
for lbl in ax.get_yticklabels():
    lbl.set_fontweight('bold')

ax.grid(True, axis='y', color=line_color, linewidth=0.6, alpha=0.25)
ax.xaxis.grid(False)

# Beschriftungen in/unter den Blasen:
fig.canvas.draw()
renderer = fig.canvas.get_renderer()

for idx, row in df.iterrows():
    x = row['x_pos']
    y = row['y_pos']
    s = row['s']
    radius_pts = np.sqrt(s) / 2.0
    radius_px = radius_pts * fig.dpi / 72.0

    val = float(row['Wert'])
    if abs(val - round(val)) < 1e-6:
        label = str(int(round(val)))
    else:
        label = f"{val:.1f}"

    # fontsize jetzt abhängig vom Radius, damit größere Labels möglich sind
    fontsize_pts = int(max(11, min(11, radius_pts * 1.2)))

    txt = ax.text(x, y, label, ha='center', va='center', fontsize=fontsize_pts, color=line_color, clip_on=False)
    bbox = txt.get_window_extent(renderer=renderer)

    fits_horizontally = bbox.width <= 2 * radius_px
    fits_vertically = bbox.height <= 2 * radius_px
    if not (fits_horizontally and fits_vertically and radius_px > 0):
        disp = ax.transData.transform((x, y))
        offset_px = radius_px + bbox.height / 2.0 + 2
        new_disp = (disp[0], disp[1] - offset_px)
        new_data = ax.transData.inverted().transform(new_disp)
        txt.set_position((x, new_data[1]))
        txt.set_verticalalignment('center')

# Legende für y-Kategorien (Energieträger)
patches = [mpatches.Patch(color=color_map[cat], label=cat) for cat in y_categories]

# Titel und Layout
ax.set_title("EEV nach Energieträgern und Sektoren im Jahr 2023 in TWh", fontsize=14, pad=15, fontweight='bold', loc='center')

# Bereich etwas erweitern, damit die äußeren Blasen nicht abgeschnitten werden
x_margin = x_spacing * 0.5
ax.set_xlim(-x_margin, ticks_x[-1] + x_margin)
sns.despine(offset=10, trim=True)
ax.set_facecolor("white")

plt.tight_layout()
plt.show()

print("Bubble Chart successfully created.")