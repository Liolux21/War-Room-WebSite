import streamlit as st
import pandas as pd
import requests
import time
import os
from datetime import datetime, timedelta

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="War Room - Sniper Dashboard", layout="wide")

# ==========================================
# 🔐 CONFIGURATION SCANNER (API FOOTBALL-DATA)
# ==========================================
API_KEY = "2a2acdc61d034feb909c10b63b916195"
COMPETITIONS = ['PL', 'PD', 'BL1', 'SA', 'FL1', 'CL', 'DED', 'PPL']
BIG_SIX = ["AFC Ajax", "PSV", "Feyenoord", "Sporting Clube de Portugal", "FC Porto", "SL Benfica"]

@st.cache_data
def load_players_db():
    file_name = "MASTER_ANALYSE_2026-04-02.csv"
    try:
        if os.path.exists(file_name):
            df = pd.read_csv(file_name)
            return df.groupby('Equipe')['Joueur'].apply(list).to_dict()
    except:
        pass
    return {}

players_db = load_players_db()

def get_force_dict(league_code, headers):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        force_dict = {}
        if 'standings' in res:
            for s in res['standings']:
                if 'table' in s:
                    for t in s['table']:
                        force_dict[t['team']['name']] = {
                            'pos': t['position'],
                            'pts': t['points'],
                            'gd': t['goalDifference']
                        }
        return force_dict
    except:
        return {}

def run_super_scanner():
    headers = {'X-Auth-Token': API_KEY}
    aujourd_hui = datetime.now()
    dans_10_jours = aujourd_hui + timedelta(days=10)
    matchs_list = []
    
    for league in COMPETITIONS:
        try:
            force_dict = get_force_dict(league, headers)
            time.sleep(1.2) # Sécurité quota API

            url_m = f"https://api.football-data.org/v4/competitions/{league}/matches?dateFrom={aujourd_hui.strftime('%Y-%m-%d')}&dateTo={dans_10_jours.strftime('%Y-%m-%d')}"
            res_m = requests.get(url_m, headers=headers, timeout=10).json()

            if 'matches' in res_m and res_m['matches']:
                for m in res_m['matches']:
                    dom = m['homeTeam']['name']
                    ext = m['awayTeam']['name']
                    
                    # FILTRE INTELLIGENT : Si Pays-Bas ou Portugal, on ne prend que le Big Six
                    if league in ['DED', 'PPL']:
                        if dom not in BIG_SIX and ext not in BIG_SIX:
                            continue

                    data_dom = force_dict.get(dom, {'pos': 10, 'pts': 0, 'gd': 0})
                    data_ext = force_dict.get(ext, {'pos': 10, 'pts': 0, 'gd': 0})
                    ecart = abs(data_dom['pos'] - data_ext['pos'])

                    matchs_list.append({
                        'Date': m['utcDate'][:10],
                        'Heure': m['utcDate'][11:16],
                        'Match': f"{dom} vs {ext}",
                        'Ligue': league,
                        'Favori': dom if data_dom['pos'] < data_ext['pos'] else ext,
                        'Confiance_Initiale': f"{min(95, 50 + (ecart * 3))}%",
                        'GO_Etape1': False, 'GO_Etape2': False, 'GO_Etape3': False
                    })
            time.sleep(1.2)
        except:
            continue
    return pd.DataFrame(matchs_list)

# 2. GESTION DES SESSIONS (Sidebar)
with st.sidebar:
    st.header("⚙️ Paramètres")
    session_active = st.selectbox("Session :", ["Week-end en cours", "Week-end prochain", "Archives"])
    if 'all_sessions' not in st.session_state:
        st.session_state.all_sessions = {}
    
    if session_active not in st.session_state.all_sessions:
        stats_cols = ['H_1x2', 'A_1x2', 'H_AH', 'A_AH', 'H_Over', 'A_Over', 'H_1stGoal', 'A_1stGoal', 'H_BTTS', 'A_BTTS', 'H_RTP', 'A_RTP', 'H_RTA', 'A_RTA', 'H_AttD', 'A_AttD', 'H_Shots', 'A_Shots', 'H_TirC', 'A_TirC', 'H_TirH', 'A_TirH']
        base_cols = ['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1', 'GO_Etape2', 'GO_Etape3', 'Absents_Dom', 'Absents_Ext', 'Cote_Cible', 'Pari_Final']
        st.session_state.all_sessions[session_active] = pd.DataFrame(columns=base_cols + stats_cols)

# 3. INTERFACE
tab1, tab2, tab3, tab4 = st.tabs(["📡 Radar", "📊 Stats", "🏥 Infirmerie", "🧮 Verdict"])

# --- ONGLET 1 : RADAR ---
with tab1:
    st.header(f"1. Radar : {session_active}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 LANCER LE SUPER SCANNER"):
            with st.spinner("Analyse des ligues + Big 6 Benelux/Portugal..."):
                new_df = run_super_scanner()
                if not new_df.empty:
                    st.session_state.all_sessions[session_active] = pd.concat([st.session_state.all_sessions[session_active], new_df]).drop_duplicates(subset=['Match', 'Date'])
                    st.success(f"{len(new_df)} matchs importés !")
                    st.rerun()
    with c2:
        if st.button("🗑️ Vider"):
            st.session_state.all_sessions[session_active] = pd.DataFrame(columns=st.session_state.all_sessions[session_active].columns)
            st.rerun()

    df_radar = st.session_state.all_sessions[session_active]
    if not df_radar.empty:
        edited = st.data_editor(df_radar[['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1']], use_container_width=True, hide_index=True,height=800)
        if st.button("💾 Sauvegarder"):
            st.session_state.all_sessions[session_active].update(edited)
            st.success("Radar enregistré !")

# --- ONGLET 2 : STATS ---
with tab2:
    current_df = st.session_state.all_sessions[session_active]
    matches = current_df[current_df['GO_Etape1'] == True]
    if matches.empty: st.info("Cochez GO au Radar.")
    else:
        for idx, row in matches.iterrows():
            with st.expander(f"⚔️ {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                labels = ["1X2 (%)", "Handicap (%)", "Over (%)", "1st Goal (%)", "BTTS (%)", "---", "RTP", "RTA", "Att. Danger", "Tirs", "Cadrés", "Hors Cadre"]
                df_d = pd.DataFrame({"Indicateur": labels, dom: [row['H_1x2'], row['H_AH'], row['H_Over'], row['H_1stGoal'], row['H_BTTS'], "", row['H_RTP'], row['H_RTA'], row['H_AttD'], row['H_Shots'], row['H_TirC'], row['H_TirH']], ext: [row['A_1x2'], row['A_AH'], row['A_Over'], row['A_1stGoal'], row['A_BTTS'], "", row['A_RTP'], row['A_RTA'], row['A_AttD'], row['A_Shots'], row['A_TirC'], row['A_TirH']]})
                edited_d = st.data_editor(df_d, key=f"d_{idx}", use_container_width=True, hide_index=True, height=500)
                if st.button(f"💾 Valider {row['Match']}", key=f"s_{idx}"):
                    st.session_state.all_sessions[session_active].at[idx, 'H_1x2'] = edited_d.iloc[0, 1]
                    st.session_state.all_sessions[session_active].at[idx, 'A_1x2'] = edited_d.iloc[0, 2]
                    st.session_state.all_sessions[session_active].at[idx, 'GO_Etape2'] = True
                    st.rerun()

# --- ONGLET 3 : INFIRMERIE ---
with tab3:
    if st.button("🔄 Récupérer blessés"):
        source = "Week-end en cours" if session_active == "Week-end prochain" else "Archives"
        if source in st.session_state.all_sessions:
            old = st.session_state.all_sessions[source]
            st.session_state['memo'] = {p['Joueur']: p for _, r in old.iterrows() for side in ['Absents_Dom', 'Absents_Ext'] if isinstance(r[side], list) for p in r[side] if p.get('Durée') == "Out"}
            st.success("Mémoire OK !")
    
    df_inf = st.session_state.all_sessions[session_active][st.session_state.all_sessions[session_active]['GO_Etape2'] == True]
    if df_inf.empty: st.info("Validez l'étape 2.")
    else:
        for idx, row in df_inf.iterrows():
            with st.expander(f"🏥 {row['Match']}"):
                dom, ext = row['Match'].split(' vs ')
                l_dom, l_ext = sorted(players_db.get(dom, [])), sorted(players_db.get(ext, []))
                i_dom = [st.session_state['memo'][p] for p in l_dom if 'memo' in st.session_state and p in st.session_state['memo']]
                i_ext = [st.session_state['memo'][p] for p in l_ext if 'memo' in st.session_state and p in st.session_state['memo']]
                c_d, c_e = st.columns(2)
                with c_d:
                    res_d = st.data_editor(pd.DataFrame(i_dom if i_dom else [], columns=['Joueur', 'Type', 'Durée']), key=f"ad_{idx}", num_rows="dynamic", column_config={"Joueur": st.column_config.SelectboxColumn("Joueur", options=l_dom), "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"]), "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"])})
                with c_e:
                    res_e = st.data_editor(pd.DataFrame(i_ext if i_ext else [], columns=['Joueur', 'Type', 'Durée']), key=f"ae_{idx}", num_rows="dynamic", column_config={"Joueur": st.column_config.SelectboxColumn("Joueur", options=l_ext), "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"]), "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"])})
                if st.checkbox(f"Valider {row['Match']}", key=f"v_{idx}"):
                    st.session_state.all_sessions[session_active].at[idx, 'GO_Etape3'] = True
                    st.session_state.all_sessions[session_active].at[idx, 'Absents_Dom'], st.session_state.all_sessions[session_active].at[idx, 'Absents_Ext'] = res_d.to_dict('records'), res_e.to_dict('records')

# --- ONGLET 4 : VERDICT ---
with tab4:
    df_f = st.session_state.all_sessions[session_active][st.session_state.all_sessions[session_active]['GO_Etape3'] == True]
    for idx, row in df_f.iterrows():
        with st.expander(f"💰 {row['Match']}"):
            c1, c2, c3 = st.columns(3)
            with c1: st.data_editor(pd.DataFrame({"M": ["1","X","2","DNB 1","DNB 2","1X","X2"], "C": [1.0]*7}), key=f"c1_{idx}", hide_index=True)
            with c2: st.data_editor(pd.DataFrame({"M": ["BTTS Oui","BTTS Non","Over 1.5","Over 2.5","Over 3.5","Under 1.5","Under 2.5","Under 3.5"], "C": [1.0]*8}), key=f"c2_{idx}", hide_index=True)
            with c3: st.data_editor(pd.DataFrame({"H": ["-0.5","+0.5"], "C Dom": [1.0, 1.0], "C Ext": [1.0, 1.0]}), key=f"c3_{idx}", hide_index=True)
            if st.button(f"📰 Prompt {row['Match']}", key=f"p_{idx}"):
                st.code(f"Analyse {row['Match']}. Absents : {row['Absents_Dom']} / {row['Absents_Ext']}")
