import pandas as pd

def normalize(series, scale=10):
    """Min-Max Normalisierung auf 0–scale"""
    return (series - series.min()) / (series.max() - series.min()) * scale

def clean_number(s):
    """Hilfsfunktion: Kommas und Prozentzeichen entfernen"""
    if pd.isna(s):
        return None
    return str(s).replace(",", "").replace("%", "").strip()

def calculate_form(input_csv="all_players_stats.csv", output_csv="all_players_with_form.csv"):
    df = pd.read_csv(input_csv, sep=";")

    # Spalten säubern
    df["Averages"] = pd.to_numeric(df["Averages"].apply(clean_number), errors="coerce")
    df["Checkout Pcnt"] = pd.to_numeric(df["Checkout Pcnt"].apply(clean_number), errors="coerce")
    df["Pcnt Legs Won"] = pd.to_numeric(df["Pcnt Legs Won"].apply(clean_number), errors="coerce")
    df["180's"] = pd.to_numeric(df["180's"].apply(clean_number), errors="coerce")

    # Normalisierung
    df["AvgNorm"] = normalize(df["Averages"])
    df["CheckoutNorm"] = normalize(df["Checkout Pcnt"])
    df["LegsNorm"] = normalize(df["Pcnt Legs Won"])
    df["180Norm"] = normalize(df["180's"])

    # Gewichtete Summe → Form Score
    df["Form"] = (
        0.4 * df["AvgNorm"] +
        0.3 * df["CheckoutNorm"] +
        0.2 * df["LegsNorm"] +
        0.1 * df["180Norm"]
    )

    # Speichern
    df.to_csv(output_csv, sep=";", index=False, encoding="utf-8")
    print(f"✅ Form-Scores berechnet und gespeichert in {output_csv}")
    print(df[["Name", "Averages", "Checkout Pcnt", "Pcnt Legs Won", "180's", "Form"]].head())

if __name__ == "__main__":
    calculate_form()
