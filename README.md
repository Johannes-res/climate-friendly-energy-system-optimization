# Optimierungsmodell für klimafreundliche Energiebereitstellung
(soon in english as well)


Hier wird eine Modellierung einer klimafreundlichen Energieversorgung für Deutschland erstellt.
Dazu wird zunächst der Verbrauch bzw. Bedarf anhand vorhandener Endenergiebedarfe und Prognosen in Zeitreihen modelliert.
Danach kann dieser Bedarf mittels Variation verschiedener regenerativen Umwandlungstechnologien gedeckt werden.
Eine Optimierung zwischen den installierten Leistungen der verschiedenen Technologien sucht unter der Hauptbedingung, dass zu jedem Zeitpunkt der Bedarf gedeckt werden kann, die Kostengünstigste technische Lösung zur Energiebereitstellung.


# Datenstruktur
Perspektivisch soll möglichst Benutzer*innenfreundlich über main.py alles gesteuert werden können.
Für mehr Übersichtlichkeit wurden einzelne .py-Dateien erstellt, welche abtrennbare Funktionen ausführen.
So gibt es momentan:

daten_einlesen.py                 Einlesen von Tabellen etc.
graphisch_darstellen.py           Plotten von Zeitreihen zur graphischen Überprüfung
last_aufteilen.py                 Aufteilen der allgemeinen Last in Verbrauchssektoren
last_prognose.py                  Erweiterung des last_aufteilen.py mit der Möglichkeit neue Verbraucherprofile und Energiebedarfe zu ergänzen
lastprofile_modellieren.py        eigenhändiges Erstellen von Lastprofilen um neue Verbraucher dynamisch mit in die Zeitreihen einfließen zu lassen



# daten_einlesen.py
Hier werden zunächst die Daten von energy-charts.info geladen sowie die Energiebilanz für Deutschland von der AGEB. Zudem werden die neuen Standardlastprofile des BDEW geladen.
Danach werden die Dataframes aufbereitet und die relevanten Daten extrahiert.

# graphisch_darstellen.py
Hier können beliebige Jahreszeitreihen importiert werden und der Jahresgang, ein einzelner Tag oder eine Woche dargestellt werden.

# last_aufteilen.py
Hier wird die Lastzeitreihe anhand der Endstromverbräuche der Sektoren sowie den Lastprofilen aufgeteilt.

# last_prog_strom.py
Macht das selbe wie last_aufteilen.py. Zusätzlich können neue Verbrauchergruppen wie zb. die Emobilität mit einem Lastprofil eingelesen und der anteil an der Last pro 15min-Wert ermittelt werden.

# last_prog_allg.py
Nutzt Funktionen aus lastprofile_modellieren um benutzerspezifische Lastprofile zu erstellen. Mittels der Funktion ergänze_Zeitreihen können diese dann an den Zeitreihendataframe aus last_prog_strom angegliedert werden und so den gesamten Energiebedarf 15min aufgelöst darstellen.

# lastprofile_modellieren.py
Schafft die Möglichkeit eigene Lastprofile in Anlehnung der Standardlastprofile des BDEW zu erstellen.
Momentan ist ein EMob_Lastprofil sowie ein Wärmpepumpen Lastprofil initialisiert.

# klimaneutral_heute.py
Ziel ist die Verschiebung der Energieträger der AGEB Energiebilanzen der letzten Jahre hinzu klimaneutralen, also primär Strom und Wasserstoff. So soll der Bedarf an klimaneutraler Energiebereitstellung auf heute bezogen dargestellt werden.

# Datenwege Verbrauch

1. klimaneutral_heute.py importiert die über daten_einlesen.py eingelesene Tabelle der Energiebilanzen und benennt die Spalten zu den Energieträgern um.Zusätzlich erfolgt die Umrechnung von TJ auf GWh. Dann wird pro Sektor jeder Energieträger dem neuen klimaneutralem Energieträger zugeordnet. Am ende erhält man pro sektor die Umsortierung, die Summe für Strom, Wasserstoff,.. und auch eine Gesamtübersicht.
2. Die Gesamtübersicht ist Datengrundlage für den Endenergiebedarf im Skript last_prog_allg.py für alle weiteren Energieträger ausser Strom.
    Der Energiebedarf an Strom aus klimaneutral_heute.py wird in last_prog_strom.py als jahresmenge eingegeben und so die Zeitreihe proportional gebildet. Diese kann dann in last_prog_allg.py einfließen und die Grundlage bilden.
3. die erstellte Zeitreihe in last_prog_allg. kann nun grapisch_darstellen.py übergeben werden und dort die interessanten Spalten und Abschnitte ausgewählt werden.
