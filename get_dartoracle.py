import requests
import pandas as pd

# API-URL
url = "https://app.dartsorakel.com/api/stats/player"

# Headers, damit die API dich akzeptiert
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

# Anfrage senden
r = requests.get(url, headers=headers)
r.raise_for_status()

# JSON-Daten laden
data = r.json()

# Liste mit Spielern extrahieren
players = []
for p in data["data"]:
    players.append({
        "name": p["player_name"].strip(),
        "country": p["country"],
        "avg": p["stat"],
        "url": f"https://app.dartsorakel.com/player/details/{p['player_key']}"
    })

# In DataFrame umwandeln
df = pd.DataFrame(players)

# CSV speichern
df.to_csv("players.csv", index=False, encoding="utf-8")

print(f"{len(df)} Spieler gespeichert → players.csv")
print(df.head())
