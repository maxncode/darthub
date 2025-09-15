import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_player_overview(player_id, player_name):
    url = f"https://app.dartsorakel.com/player/stats/{player_id}"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/html"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # Basisdaten
    stats = {"Id": player_id, "Name": player_name}

    # Stats-Tabelle auslesen
    stats_table = soup.find("table", {"id": "playerStatsTable"})
    if stats_table:
        for tr in stats_table.find("tbody").find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) == 2:
                stat_name = tds[0].get_text(strip=True)
                stat_value = tds[1].get_text(strip=True)
                stats[stat_name] = stat_value

    return stats


if __name__ == "__main__":
    # Spielerbasis laden
    players_df = pd.read_csv("players.csv")

    all_stats = []
    for _, row in players_df.iterrows():
        name = row["name"]
        url = row["url"]
        player_id = url.split("/")[-1]  # ID aus URL extrahieren
        print(f"Hole Stats für {name} (ID {player_id}) ...")

        stats = get_player_overview(player_id, name)
        all_stats.append(stats)

    # Alles in eine CSV
    df = pd.DataFrame(all_stats)
    filename = "all_players_stats.csv"
    df.to_csv(filename, sep=";", index=False, encoding="utf-8")
    print(f"✅ {len(df)} Spieler-Stats gespeichert in {filename}")
    print(df.head())
