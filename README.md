# Optimierungsmodell für klimafreundliche Energiebereitstellung
(soon in english as well)


Hier wird eine Modellierung einer klimafreundlichen Energieversorgung für Deutschland erstellt.
Dazu wird zunächst der Verbrauch bzw. Bedarf anhand vorhandener Endenergiebedarfe und Prognosen in Zeitreihen modelliert.
Danach kann dieser Bedarf mittels Variation verschiedener regenerativen Umwandlungstechnologien gedeckt werden.
Eine Optimierung zwischen den installierten Leistungen der verschiedenen Technologien sucht unter der Hauptbedingung, dass zu jedem Zeitpunkt der Bedarf gedeckt werden kann, die Kostengünstigste technische Lösung zur Energiebereitstellung.


# Datenstruktur
Im Ordner data befinden sich alle Daten für die Eingabe und die der Ausgabe.
Im Ordner scripts_opt_neu sind alle python Skripte zur Druchführung der Optimierung, Grafikerstellung und Vorbereitung der Daten abgelegt.

Am Anfang jedes Skripts werden die Daten aus data eingelesen, am Ende an einem definierten Ort innerhalb data abgelegt. Es müssen die notwendigen Module für jedes Skript vorhanden und installiert sein.
Die Skripte sind momentan meistens eigenständig, so dass auf bereits erzeugte Daten aus vorherigen Skripten zugegriffen wird und diese einzelen neu eingelesen werden.
Dadurch sind die Datenpfade und die Reinfolge der Skripte nachvollziehbar.

Grundlegend wird mit der Ermittlung des Bedarfes gestartet.
Dies geschiet in den einzelen Bedarfsskripten unter a_Eingangsdaten.
Danach werden diese in x_Bedarf_gesamt summiert und bilden Ausgangspunkt der Optimierung.

Unter b_Optimierung findet die Optimierung mit ihren einzelen Bestandteilen statt. Es muss bei a_inputs.py überprüft werden welche Daten eingelesen werden sollen und bei f_speichern.py, mit welchen Namen und wohin die Ergebnisse gespeichert werden sollen.
Es werden die zuvor erzeugten Bedarfszeitreihen eingelesen sowie die Optimierungsvariablen und festgelegte Grenz-/Nebenbedingungswerte.
Durch Ausführen der main.py wird die gesamte Optimierung durchlaufen.

Unter c_Auswertung können neben weiteren statistischen Werten auch Grafiken der Bedarfe und Erzeuger erstellt werden.
Die Daten sind im gleichbenannten Ordner unter data einzusehen.

Innerhalb der Skripte können die Variationen stattfinden. Dazu sei die Modellvariante zu ändern und die gewünschten Variationen durchzuführen.


Liste der wichtigsten notwendigen Module:
- pandas - Tabellenhandling
- meteostat - Wetterdaten
- pyomo - Optimierungsumgebung
- cbc - Löser für Optimierung
- seaborn - Grafische Darstellung
- matplotlib - Grafische Darstellung
- numpy - mathemaisches Handling
- holidays - Ferientage
- datetime - Datumshandling

