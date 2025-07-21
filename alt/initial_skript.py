
import pandas as pd

df = pd.read_excel(r'data\Endenergiebedarf_AGEB\EBD22e.xlsx')



df.set_index(df.columns[0], inplace=True)

# Funktion, die mehrere Werte aus einem DataFrame holt
def get_values_from_dataframe(df, queries):
    """
    Holt mehrere Werte aus einem DataFrame basierend auf einer Liste von Abfragen.

    :param df: Der DataFrame, aus dem die Werte geholt werden sollen.
    :param queries: Eine Liste von Tupeln (row_name, column_name), die die gewünschten Einträge spezifizieren.
    :return: Ein DataFrame mit den Ergebnissen.
    """
    results = []
    for row_name, column_name in queries:
        try:
            value = df.loc[row_name, column_name]
            results.append({'Row': row_name, 'Column': column_name, 'Value': value})
        except KeyError:
            results.append({'Row': row_name, 'Column': column_name, 'Value': 'Fehler: Nicht gefunden'})
    return pd.DataFrame(results)

# Beispielaufruf der Funktion
queries = [
    ('ENDENERGIEVERBRAUCH', 'Unnamed: 34'),
    ('Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe', 'Unnamed: 34'),
    ('Verkehr insgesamt', 'Unnamed: 34'),
    ('Haushalte, Gewerbe, Handel und Dienstleistungen', 'Unnamed: 34')
]

df_answer = get_values_from_dataframe(df, queries)


df_neu=pd.DataFrame()
df_neu['Summe'] = df_answer.set_index('Row')['Value']  # Setzt 'Row' als Index und übernimmt die Werte aus 'Value'


# Beispielaufruf der Funktion
queries = [
    ('ENDENERGIEVERBRAUCH', 'Unnamed: 29'),
    ('Bergbau, Gew. v. Steinen u. Erden, Verarb. Gewerbe', 'Unnamed: 29'),
    ('Verkehr insgesamt', 'Unnamed: 29'),
    ('Haushalte, Gewerbe, Handel und Dienstleistungen', 'Unnamed: 29')
]

df_answer = get_values_from_dataframe(df, queries)
df_neu['Strom'] = df_answer.set_index('Row')['Value']  # Ergänzt die Werte aus 'Value' passend zum Index

