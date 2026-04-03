import streamlit as st
import pandas as pd
import requests
import time
import os
from datetime import datetime, timedelta

# 1. CONFIGURATION
st.set_page_config(page_title="War Room - Sniper Dashboard", layout="wide")

# ==========================================
# 🔐 CONFIGURATION API & FILTRES CIBLÉS
# ==========================================
API_KEY = "2a2acdc61d034feb909c10b63b916195"
COMPETITIONS = ['PL', 'PD', 'BL1', 'SA', 'FL1', 'CL', 'DED', 'PPL']

# Noms EXACTS utilisés par l'API football-data.org pour tes cibles
BIG_SIX_NAMES = [
    "AFC Ajax", "PSV", "Feyenoord",           # Eredivisie
    "Sporting CP", "FC Porto", "SL Benfica"   # Primeira Liga
]

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

# ==========================================
# 📡 FONCTIONS DE SCAN
# ==========================================
def get_target_dates(session_name):
    today = datetime.now()
    # On cherche le vendredi (4) de la semaine
    days_to_friday = (4 - today.weekday())
    
    # Si on est WE, on prend le vendredi qui vient de passer pour voir les matchs en cours
    start_of_we = today + timedelta(days=days_to_friday)
    
    if session_name == "Week-end prochain":
        start_date = start_of_we + timedelta(days=7)
    else:
        start_date = start_of_we
        
    end_date = start_date + timedelta(days=3) # Jusqu'au lundi inclus
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

def get_force_dict(league_code, headers):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        force_dict = {}
        if 'standings' in res:
            for s in res['standings']:
                if s['type'] == 'TOTAL':
                    for t in s['table']:
                        force_dict[t['team']['name']] = {'pos': t['position'], 'pts': t['points'], 'gd': t['goalDifference']}
        return force_dict
    except: return {}

def run_super_scanner(session_name):
    headers = {'X-Auth-Token': API_KEY}
    date_from, date_to = get_target_dates(session_name)
    matchs_list = []
    
    progress_bar = st.progress(0)
    for i, league in enumerate(COMPETITIONS):
        progress_bar.progress((i + 1) / len(COMPETITIONS))
        try:
            force_dict = get_force_dict(league, headers)
            time.sleep(1.2) # Quota API

            url_m = f"https://api.football-data.org/v4/competitions/{league}/matches?dateFrom={date_from}&dateTo={date_to}"
            res_m = requests.get(url_m, headers=headers, timeout=10).json()

            if 'matches' in res_m and res_m['matches']:
                for m in res_m['matches']:
                    dom = m['homeTeam']['name']
                    ext = m['awayTeam']['name']
                    
                    # FILTRE CIBLÉ : Uniquement les gros pour DED et PPL
                    if league in ['DED', 'PPL']:
                        if dom not in BIG_SIX_NAMES and ext not in BIG_SIX_NAMES:
                            continue

                    d_dom = force_dict.get(dom, {'pos': 10, 'pts': 0, 'gd': 0})
                    d_ext = force_dict.get(ext, {'pos': 10, 'pts': 0, 'gd': 0})
                    ecart = abs(d_dom['pos'] - d_ext['pos'])

                    matchs_list.append({
                        'Date': m['utcDate'][:10],
                        'Heure': m['utcDate'][11:16],
                        'Match': f"{dom} vs {ext}",
                        'Ligue': league,
                        'Favori': dom if d_dom['pos'] < d_ext['pos'] else ext,
                        'Confiance_Initiale': f"{min(95, 50 + (ecart * 3))}%",
                        'GO_Etape1': False, 'GO_Etape2': False, 'GO_Etape3': False,
                        'H_1x2':0,'A_1x2':0,'H_AH':0,'A_AH':0,'H_Over':0,'A_Over':0,'H_1stGoal':0,'A_1stGoal':0,'H_BTTS':0,'A_BTTS':0,
                        'H_RTP':0,'A_RTP':0,'H_RTA':0,'A_RTA':0,'H_AttD':0,'A_AttD':0,'H_Shots':0,'A_Shots':0,'H_TirC':0,'A_TirC':0,'H_TirH':0,'A_TirH':0,
                        'Absents_Dom':[], 'Absents_Ext':[], 'Cote_Cible':0, 'Pari_Final':''
                    })
            time.sleep(1.2)
        except: continue
    return pd.DataFrame(matchs_list)

# ==========================================
# ⚙️ GESTION SESSIONS
# ==========================================
with st.sidebar:
    st.header("⚙️ Paramètres")
    session_active = st.selectbox("Session de travail :", ["Week-end en cours", "Week-end prochain", "Archives"])
    if 'all_sessions' not in st.session_state:
        st.session_state.all_sessions = {}
    if session_active not in st.session_state.all_sessions:
        st.session_state.all_sessions[session_active] = pd.DataFrame()

# ==========================================
# 🏗️ INTERFACE
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["📡 Radar", "📊 Stats (Duel)", "🏥 Infirmerie", "🧮 Verdict"])

# --- ONGLET 1 : RADAR ---
with tab1:
    st.header(f"Radar : {session_active}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 LANCER LE SUPER SCANNER"):
            new_df = run_super_scanner(session_active)
            if not new_df.empty:
                st.session_state.all_sessions[session_active] = new_df.sort_values(by=['Date', 'Heure'])
                st.rerun()
    with c2:
        if st.button("🗑️ Vider"):
            st.session_state.all_sessions[session_active] = pd.DataFrame()
            st.rerun()

    df_radar = st.session_state.all_sessions[session_active]
    if not df_radar.empty:
        edited = st.data_editor(df_radar[['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1']], use_container_width=True, hide_index=True, height=600)
        if st.button("💾 Sauvegarder"):
            st.session_state.all_sessions[session_active].update(edited)
            st.success("Radar enregistré !")

# --- ONGLET 2 : STATS ---
with tab2:
    cur_df = st.session_state.all_sessions[session_active]
    if cur_df.empty: st.warning("Lancez un scan.")
    else:
        matches = cur_df[cur_df['GO_Etape1'] == True]
        if matches.empty: st.info("Cochez GO au Radar.")
        for idx, row in matches.iterrows():
            with st.expander(f"⚔️ {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                labels = ["1X2 (%)", "AH (%)", "Over (%)", "1stG (%)", "BTTS (%)", "---", "RTP", "RTA", "Att.D", "Tirs", "Cadrés", "Hors C."]
                df_d = pd.DataFrame({"Indicateur": labels, dom: [row['H_1x2'], row['H_AH'], row['H_Over'], row['H_1stGoal'], row['H_BTTS'], "", row['H_RTP'], row['H_RTA'], row['H_AttD'], row['H_Shots'], row['H_TirC'], row['H_TirH']], ext: [row['A_1x2'], row['A_AH'], row['A_Over'], row['A_1stGoal'], row['A_BTTS'], "", row['A_RTP'], row['A_RTA'], row['A_AttD'], row['A_Shots'], row['A_TirC'], row['A_TirH']]})
                edited_d = st.data_editor(df_d, key=f"d_{idx}", use_container_width=True, height=500)
                if st.button(f"💾 Valider {row['Match']}", key=f"s_{idx}"):
                    st.session_state.all_sessions[session_active].at[idx, 'GO_Etape2'] = True
                    st.rerun()

# --- ONGLET 3 : INFIRMERIE ---
with tab3:
    if st.button("🔄 Récupérer mémoire"):
        source = "Week-end en cours" if session_active == "Week-end prochain" else "Archives"
        if source in st.session_state.all_sessions:
            old = st.session_state.all_sessions[source]
            st.session_state['memo'] = {p['Joueur']: p for _, r in old.iterrows() for side in ['Absents_Dom', 'Absents_Ext'] if isinstance(r[side], list) for p in r[side] if p.get('Durée') == "Out"}
            st.success("Mémoire chargée.")

    cur_inf = st.session_state.all_sessions[session_active]
    df_inf = cur_inf[cur_inf['GO_Etape2'] == True]
    if df_inf.empty: st.info("Validez l'étape 2.")
    else:
        for idx, row in df_inf.iterrows():
            with st.expander(f"🏥 {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                l_dom, l_ext = sorted(players_db.get(dom, [])), sorted(players_db.get(ext, []))
                i_dom = [st.session_state['memo'][p] for p in l_dom if 'memo' in st.session_state and p in st.session_state['memo']]
                i_ext = [st.session_state['memo'][p] for p in l_ext if 'memo' in st.session_state and p in st.session_state['memo']]
                c_d, c_e = st.columns(2)
                with c_d:
                    res_d = st.data_editor(pd.DataFrame(i_dom if i_dom else [], columns=['Joueur', 'Type', 'Durée']), key=f"ad_{idx}", num_rows="dynamic", use_container_width=True, column_config={"Joueur": st.column_config.SelectboxColumn("Joueur", options=l_dom), "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"]), "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"])})
                with c_e:
                    res_e = st.data_editor(pd.DataFrame(i_ext if i_ext else [], columns=['Joueur', 'Type', 'Durée']), key=f"ae_{idx}", num_rows="dynamic", use_container_width=True, column_config={"Joueur": st.column_config.SelectboxColumn("Joueur", options=l_ext), "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"]), "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"])})
                if st.checkbox(f"Valider {row['Match']}", key=f"v_{idx}"):
                    st.session_state.all_sessions[session_active].at[idx, 'GO_Etape3'] = True
                    st.session_state.all_sessions[session_active].at[idx, 'Absents_Dom'], st.session_state.all_sessions[session_active].at[idx, 'Absents_Ext'] = res_d.to_dict('records'), res_e.to_dict('records')

# --- ONGLET 4 : VERDICT ---
with tab4:
    df_f = st.session_state.all_sessions[session_active][st.session_state.all_sessions[session_active]['GO_Etape3'] == True]
    for idx, row in df_f.iterrows():
        with st.expander(f"💰 {row['Match']}"):
            c1, c2, c3 = st.columns(3)
            with c1: st.data_editor(pd.DataFrame({"Marché": ["1","X","2","DNB 1","DNB 2","1X","X2"], "Cote": [1.0]*7}), key=f"c1_{idx}", hide_index=True)
            with c2: st.data_editor(pd.DataFrame({"Marché": ["BTTS Oui","BTTS Non","Over 1.5","Over 2.5","Over 3.5","Under 1.5","Under 2.5","Under 3.5"], "Cote": [1.0]*8}), key=f"c2_{idx}", hide_index=True)
            with c3: st.data_editor(pd.DataFrame({f"Hdc {dom}": ["-0.5","+0.5"], "Cote Dom": [1.0, 1.0], f"Hdc {ext}": ["-0.5","+0.5"], "Cote Ext": [1.0, 1.0]}), key=f"c3_{idx}", hide_index=True)
            if st.button(f"📰 Prompt {row['Match']}", key=f"p_{idx}"):
                st.code(f"Analyse {row['Match']}. Absents : {row['Absents_Dom']} / {row['Absents_Ext']}")
