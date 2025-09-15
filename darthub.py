# darthub.py
import re
import os
import sys
import time
import random
import subprocess
from collections import Counter

import pandas as pd
import streamlit as st

# unsere Simulator-Klassen
from simulate_player import SimulatedPlayer
from simulate_match import MatchSimulator

# ---------------------
# Hilfsfunktionen
# ---------------------
def parse_number(x, default=None):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return default
    try:
        s = str(x).strip()
        if s == "":
            return default
        s = re.sub(r"[^\d\.,\-]", "", s)
        if "." in s and "," in s:
            if s.find(".") < s.find(","):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s and "." not in s:
            s = s.replace(",", ".")
        return float(s)
    except:
        return default

def run_pipeline_ui(progress_container, log_container):
    steps = [
        (["get_dartoracle.py"], "Spielerübersicht scrapen (players.csv)"),
        (["get_player_stats.py"], "Spieler-Stats scrapen (all_players_stats.csv)"),
        (["calculate_form.py"], "Form berechnen (all_players_with_form.csv)"),
    ]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    for i, (cmd, desc) in enumerate(steps, start=1):
        log_container.info(f"⏳ {desc} ...")
        proc = subprocess.run([sys.executable] + cmd, capture_output=True, text=True, env=env)
        if proc.returncode != 0:
            log_container.error(f"❌ Fehler bei '{desc}':\n\n{proc.stderr}")
            return False
        if proc.stdout:
            log_container.code(proc.stdout)
        progress_container.progress(i / len(steps))
        time.sleep(0.2)
    log_container.success("✅ Pipeline fertig – Daten aktualisiert!")
    return True

def estimate_p180_from_history(p, avg_legs_per_match=8):
    # tries to compute a reasonable per-visit 180 probability
    total_180s = None
    for cand in ["180's", "180s", "Total180s", "Total 180s"]:
        if cand in p:
            total_180s = parse_number(p[cand], None)
            if total_180s is not None:
                break
    matches = None
    for cand in ["Matches_Played", "Matches", "MatchesPlayed", "Matches Played", "match_count"]:
        if cand in p:
            matches = parse_number(p[cand], None)
            if matches is not None:
                break
    if total_180s and matches and matches > 0:
        per_leg = total_180s / (matches * avg_legs_per_match)
        # clamp
        return float(max(0.002, min(per_leg, 0.5)))
    # fallback estimate from average
    avg = parse_number(p.get("Averages", p.get("Avg", None)), 90.0)
    est = 0.03 + max(0.0, (avg - 80.0)) * 0.008
    return float(min(max(est, 0.005), 0.30))

# ---------------------
# App Start
# ---------------------
CSV_FILE = "all_players_with_form.csv"
st.set_page_config(page_title="🎯 DartsHub", layout="wide")

# Sidebar - Pipeline
st.sidebar.title("⚙️ Datenverwaltung")
progress_placeholder = st.sidebar.empty()
log_placeholder = st.sidebar.empty()

if st.sidebar.button("🔄 Daten neu laden (Pipeline starten)"):
    progress_bar = st.sidebar.progress(0)
    success = run_pipeline_ui(progress_bar, log_placeholder)
    if success:
        st.experimental_rerun()

if os.path.exists(CSV_FILE):
    modified_time = os.path.getmtime(CSV_FILE)
    st.sidebar.info(f"📅 Letztes Update: {time.strftime('%d.%m.%Y %H:%M', time.localtime(modified_time))}")
else:
    st.sidebar.warning("⚠️ Noch keine Daten vorhanden. Bitte Pipeline starten!")

# CSV laden (oder stoppen)
try:
    df = pd.read_csv(CSV_FILE, sep=";")
    df.columns = [c.strip() for c in df.columns]
except Exception as e:
    st.error(f"❌ Fehler beim Laden der CSV: {e}")
    st.stop()

# Navigation
st.sidebar.title("📂 Navigation")
page = st.sidebar.radio("Seite auswählen:", ["👤 Spielerprofil", "🎲 Match Simulation"])

# -----------------
# Spielerprofil
# -----------------
if page == "👤 Spielerprofil":
    st.title("👤 Spielerprofil")
    st.sidebar.header("🔍 Spieler Suche")
    search = st.sidebar.text_input("Name eingeben...")

    if "Name" not in df.columns:
        st.error("❌ CSV enthält keine Spalte 'Name'")
        st.stop()

    filtered = df[df["Name"].str.contains(search, case=False, na=False)] if search else df
    if filtered.empty:
        st.warning("⚠️ Kein Spieler gefunden")
        st.stop()
    selected = st.sidebar.selectbox("👤 Spieler auswählen", sorted(filtered["Name"].unique()))
    player_data = df[df["Name"] == selected].iloc[0]

    st.subheader(f"📊 Stats für {selected} (letzte 12 Monate)")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎯 Average", player_data.get("Averages", player_data.get("Avg", "n/a")))
    with col2:
        st.metric("💥 180s gesamt", player_data.get("180's", "n/a"))
    with col3:
        st.metric("✅ Checkout %", player_data.get("Checkout Pcnt", "n/a"))
    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("🏆 Legs Won %", player_data.get("Pcnt Legs Won", "n/a"))
    with col5:
        st.metric("🔝 Highest Checkout", player_data.get("Highest Checkout", "n/a"))
    with col6:
        form_value = parse_number(player_data.get("Form", 0), 0.0)
        st.metric("🔥 Form", f"{form_value}/10")

    st.divider()
    st.subheader("📈 Performance Breakdown (Text)")
    stat_cols = {
        "Averages": "Average",
        "180's": "180s",
        "Checkout Pcnt": "Checkout %",
        "Pcnt Legs Won": "Legs Won %",
        "Highest Checkout": "High Checkout",
        "Form": "Form"
    }
    for col, label in stat_cols.items():
        if col in df.columns:
            st.write(f"**{label}:** {player_data[col]}")

# -----------------
# Match Simulation
# -----------------
if page == "🎲 Match Simulation":
    st.title("🎲 Match Simulation")
    left, right = st.columns([1,1])
    with left:
        player1 = st.selectbox("👤 Spieler 1", df["Name"].unique(), index=0)
    with right:
        player2 = st.selectbox("👤 Spieler 2", df["Name"].unique(), index=1)

    if player1 == player2:
        st.warning("⚠️ Bitte zwei verschiedene Spieler auswählen")
        st.stop()

    mode = st.radio("⚖️ Match Format", ["Best of Legs", "Best of Sets"])
    if mode == "Best of Legs":
        best_of = st.selectbox("Best of wie viele Legs?", [3,5,7,9,11,13,15,17,19])
        legs_to_win = (best_of // 2) + 1
    else:
        sets = st.selectbox("Best of wie viele Sets?", [3,5,7,9])
        legs_per_set = st.selectbox("Legs pro Set", [3,5,7])
        # einfache Behandlung: treat as (sets, legs_per_set) for now; Monte Carlo supports legs only currently
        legs_to_win = None

    st.markdown("**Simulation-Modus**")
    sim_mode = st.selectbox("Modus:", ["Live (Wurf-für-Wurf)", "Monte Carlo (viele Matches)"])

    # Optionen
    if sim_mode == "Live (Wurf-für-Wurf)":
        delay = st.slider("Delay pro Aufnahme (Sekunden)", 0.1, 2.0, 0.6, 0.1)
    else:
        simulations = st.slider("Anzahl Monte-Carlo-Simulationen", 100, 5000, 1000, 100)

    # prepare player objects
    p1_row = df[df["Name"] == player1].iloc[0]
    p2_row = df[df["Name"] == player2].iloc[0]

    # build stats dicts (p180_per_leg if available)
    p1_stats = {}
    p2_stats = {}
    p1_p180 = estimate_p180_from_history(p1_row)
    p2_p180 = estimate_p180_from_history(p2_row)
    p1_stats["p180_per_leg"] = p1_p180
    p2_stats["p180_per_leg"] = p2_p180

    # create simulated players
    p1_sim = SimulatedPlayer(
        player1,
        avg=parse_number(p1_row.get("Averages", p1_row.get("Avg", 90)), 90.0),
        checkout_pct=parse_number(p1_row.get("Checkout Pcnt", 35), 35.0),
        form=parse_number(p1_row.get("Form", 5), 5.0),
        stats={"p180_per_leg": p1_p180}
    )
    p2_sim = SimulatedPlayer(
        player2,
        avg=parse_number(p2_row.get("Averages", p2_row.get("Avg", 90)), 90.0),
        checkout_pct=parse_number(p2_row.get("Checkout Pcnt", 35), 35.0),
        form=parse_number(p2_row.get("Form", 5), 5.0),
        stats={"p180_per_leg": p2_p180}
    )

    # ACTIONS
    if sim_mode == "Live (Wurf-für-Wurf)":
        if legs_to_win is None:
            st.info("Live-Modus unterstützt momentan nur Best-of-Legs. Wähle 'Best of Legs'.")
        else:
            if st.button("▶️ Live Simulation starten"):
                sim = MatchSimulator(p1_sim, p2_sim, legs_to_win=legs_to_win)
                placeholder = st.empty()
                lines = []
                for event in sim.play_match_live(delay=delay):
                    lines.append(event)
                    # show full history as text block (keeps scrollable)
                    placeholder.text("\n".join(lines[-200:]))  # zeige nur die letzten 200 Zeilen für Performance
                # am Ende evtl. Zusammenfassung
                st.success("Live-Simulation beendet.")

    else:  # Monte Carlo
        if st.button("🚀 Monte Carlo Simulation starten"):
            if legs_to_win is None:
                st.info("Monte Carlo unterstützt derzeit nur Best of Legs (no sets). Wähle 'Best of Legs'.")
            else:
                # run many matches (non-live)
                winners = []
                scorelines = []
                total_180s_p1 = []
                total_180s_p2 = []
                total_legs_list = []

                progress = st.progress(0)
                for i in range(simulations):
                    sim = MatchSimulator(
                        SimulatedPlayer(player1, p1_sim.avg, p1_sim.checkout_pct, p1_sim.form, stats=p1_sim.stats),
                        SimulatedPlayer(player2, p2_sim.avg, p2_sim.checkout_pct, p2_sim.form, stats=p2_sim.stats),
                        legs_to_win=legs_to_win
                    )
                    winner, scoreline, match_history = sim.play_match()
                    # collect stats: count 180s in match_history
                    p1_180 = 0
                    p2_180 = 0
                    total_legs = 0
                    for starter, leg_winner, leg_hist, leg_180s in match_history:
                        p1_180 += leg_180s.get(player1, 0)
                        p2_180 += leg_180s.get(player2, 0)
                        total_legs += 1
                    winners.append(winner)
                    scorelines.append(scoreline)
                    total_180s_p1.append(p1_180)
                    total_180s_p2.append(p2_180)
                    total_legs_list.append(total_legs)
                    if i % max(1, simulations//100) == 0:
                        progress.progress(i / simulations)
                progress.progress(1.0)

                win_count = Counter(winners)
                score_count = Counter(scorelines)

                st.subheader("📊 Monte Carlo Resultate")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(f"🏆 {player1} Siegwahrscheinlichkeit", f"{(win_count[player1]/simulations)*100:.1f}%")
                    st.metric(f"💥 Ø 180s {player1}", f"{(sum(total_180s_p1)/len(total_180s_p1)):.2f}")
                with col2:
                    st.metric(f"🏆 {player2} Siegwahrscheinlichkeit", f"{(win_count[player2]/simulations)*100:.1f}%")
                    st.metric(f"💥 Ø 180s {player2}", f"{(sum(total_180s_p2)/len(total_180s_p2)):.2f}")

                st.divider()
                st.subheader("📜 Häufigste Endstände (Top 10)")
                for score, count in score_count.most_common(10):
                    st.write(f"**{score}** – {count}x ({(count / simulations) * 100:.1f}%)")

                st.divider()
                st.subheader("📋 Weitere Statistiken")
                st.write(f"📌 Ø Legs pro Spiel: {(sum(total_legs_list)/len(total_legs_list)):.2f}")
                st.write(f"📌 Ø 180s Gesamt {player1}: {(sum(total_180s_p1)/len(total_180s_p1)):.2f}")
                st.write(f"📌 Ø 180s Gesamt {player2}: {(sum(total_180s_p2)/len(total_180s_p2)):.2f}")
