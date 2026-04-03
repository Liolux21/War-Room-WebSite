import streamlit as st
import pandas as pd
import requests
import time
import os
import json
from datetime import datetime, timedelta

# 1. CONFIGURATION
st.set_page_config(page_title="War Room - Sniper Dashboard", layout="wide")

# ==========================================
# 🔐 CONFIGURATION & DATA
# ==========================================
API_KEY = "2a2acdc61d034feb909c10b63b916195"
COMPETITIONS = ['PL', 'PD', 'BL1', 'SA', 'FL1', 'CL', 'DED', 'PPL']
BIG_SIX_KEYWORDS = ["Ajax", "PSV", "Feyenoord", "Sporting", "Porto", "Benfica"]

REFEREES_DB = {
    'PL': ["Anthony Taylor", "Michael Oliver", "Paul Tierney", "Simon Hooper", "Chris Kavanagh"],
    'PD': ["Gil Manzano", "Sánchez Martínez", "Munuera Montero", "Alberola Rojas"],
    'BL1': ["Felix Zwayer", "Deniz Aytekin", "Daniel Siebert", "Tobias Stieler"],
    'SA': ["Daniele Orsato", "Davide Massa", "Marco Guida", "Fabio Maresca"],
    'FL1': ["Benoît Bastien", "François Letexier", "Clément Turpin", "Stéphanie Frappart"],
    'DED': ["Danny Makkelie", "Serdar Gözübüyük", "Allard Lindhout"],
    'PPL': ["Artur Soares Dias", "Tiago Martins", "Fabio Verissimo"],
    'CL': ["Szymon Marciniak", "Slavko Vincic", "István Kovács"]
}
ALL_REFEREES = sorted(list(set([ref for sub in REFEREES_DB.values() for ref in sub])))

STATS_COLS = ['H_1x2', 'A_1x2', 'H_AH', 'A_AH', 'H_Over', 'A_Over', 'H_1stGoal', 'A_1stGoal', 'H_BTTS', 'A_BTTS', 'H_RTP', 'A_RTP', 'H_RTA', 'A_RTA', 'H_AttD', 'A_AttD', 'H_Shots', 'A_Shots', 'H_TirC', 'A_TirC', 'H_TirH', 'A_TirH']
BASE_COLS = ['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1', 'GO_Etape2', 'GO_Etape3', 'Absents_Dom', 'Absents_Ext']
VERDICT_COLS = ['Conf_AIStats', 'Conf_FotMob', 'Type_Pari', 'Palier_Snowball', 'Meteo', 'Arbitre', 'Pari_Final']
ALL_COLS = BASE_COLS + STATS_COLS + VERDICT_COLS

@st.cache_data
def load_players_db():
    file_name = "MASTER_ANALYSE_2026-04-02.csv"
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name)
            return df.groupby('Equipe')['Joueur'].apply(list).to_dict()
        except: return {}
    return {}

players_db = load_players_db()

# CORRECTEUR INTELLIGENT DE NOMS D'ÉQUIPES (Pour Monaco, etc.)
def get_roster(team_name, db):
    if team_name in db:
        return sorted(db[team_name])
    name_clean = team_name.lower().replace('fc', '').replace('as ', '').replace('cf', '').strip()
    for db_team, players in db.items():
        db_clean = db_team.lower().replace('fc', '').replace('as ', '').replace('cf', '').strip()
        if name_clean in db_clean or db_clean in name_clean:
            return sorted(players)
    return []

# --- LOGIQUE DATES & SCAN ---
def get_target_dates(session_name):
    today = datetime.now()
    days_to_friday = (4 - today.weekday())
    start_of_we = today + timedelta(days=days_to_friday)
    start_date = start_of_we + timedelta(days=7) if session_name
