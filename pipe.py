import streamlit as st
import subprocess
import sys
import os

# ==========================
# Hilfsfunktion
# ==========================
def run_step(cmd, description, progress, step, total_steps):
    st.write(f"### 🚀 {description}")
    progress.progress(step / total_steps)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"  # <- Fix für Unicode-Fehler

    result = subprocess.run(
        [sys.executable] + cmd,
        capture_output=True,
        text=True,
        env=env
    )

    if result.stdout:
        st.text(result.stdout)
    if result.stderr:
        st.error(f"⚠️ Fehler bei {description}:\n{result.stderr}")

# ==========================
# Pipeline starten
# ==========================
def run_pipeline():
    steps = [
        (["get_dartoracle.py"], "Spielerübersicht scrapen (players.csv)"),
        (["get_player_stats.py"], "Spieler-Stats scrapen (all_players_stats.csv)"),
        (["calculate_form.py"], "Form berechnen (all_players_with_form.csv)"),
    ]

    progress = st.progress(0)
    total_steps = len(steps)

    for i, (cmd, desc) in enumerate(steps, start=1):
        run_step(cmd, desc, progress, i, total_steps)

    progress.progress(1.0)
    st.success("✅ Pipeline fertig – alle Daten stehen bereit!")
