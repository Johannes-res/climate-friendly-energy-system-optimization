import requests
import pandas as pd
import io

# URL der XML-Datei
#bei 'Start' kann das Startdatum angegeben werden, bei 'End' das Enddatum
#hier wird das Startdatum auf den 01.10.2022 und das Enddatum auf den 31.10.2022 gesetzt
url = "https://transparency.entsoe.eu/load-domain/r2/totalLoadR2/show?name=&defaultValue=false&viewType=TABLE&areaType=CTY&atch=false&dateTime.dateTime=01.01.2022+00:00|UTC|DAY&biddingZone.values=CTY|10Y1001A1001A83F!CTY|10Y1001A1001A83F&dateTime.timezone=UTC&dateTime.timezone_input=UTC#"

try:
    # Excel-Datei herunterladen
    response = requests.get(url)
    response.raise_for_status()  # Wirft eine Ausnahme für ungültige Statuscodes
    
    # Inhalt der Antwort als Bytes speichern
    excel_file = io.BytesIO(response.content)

    # Excel-Datei in DataFrame einlesen (Annahme: erstes Sheet)
    df = pd.read_excel(excel_file, engine='openpyxl')

    # DataFrame anzeigen
    print(df)

except requests.exceptions.RequestException as e:
    print(f"Fehler beim Herunterladen der Datei: {e}")
except pd.errors.ParserError as e:
    print(f"Fehler beim Einlesen der Excel-Datei: {e}")
except Exception as e:
    print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")