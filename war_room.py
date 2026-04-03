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

# --- Base de données Arbitres (Exemples principaux par ligue) ---
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

# Liste plate pour la configuration du data_editor
ALL_REFEREES = sorted(list(set([ref for sub in REFEREES_DB.values() for ref in sub])))

# Colonnes
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

# --- LOGIQUE DATES & SCAN ---
def get_target_dates(session_name):
    today = datetime.now()
    days_to_friday = (4 - today.weekday())
    start_of_we = today + timedelta(days=days_to_friday)
    start_date = start_of_we + timedelta(days=7) if session_name == "Week-end prochain" else start_of_we
    return start_date.strftime('%Y-%m-%d'), (start_date + timedelta(days=3)).strftime('%Y-%m-%d')

def run_super_scanner(session_name):
    headers = {'X-Auth-Token': API_KEY}
    date_from, date_to = get_target_dates(session_name)
    matchs_list = []
    pb = st.progress(0)
    for i, league in enumerate(COMPETITIONS):
        pb.progress((i + 1) / len(COMPETITIONS))
        try:
            url_m = f"https://api.football-data.org/v4/competitions/{league}/matches?dateFrom={date_from}&dateTo={date_to}"
            res_m = requests.get(url_m, headers=headers, timeout=10).json()
            if 'matches' in res_m and res_m['matches']:
                for m in res_m['matches']:
                    dom, ext = m['homeTeam']['name'], m['awayTeam']['name']
                    if league in ['DED', 'PPL'] and not any(kw in dom or kw in ext for kw in BIG_SIX_KEYWORDS): continue
                    row = {c: "" for c in ALL_COLS}
                    row.update({'Date': m['utcDate'][:10], 'Heure': m['utcDate'][11:16], 'Match': f"{dom} vs {ext}", 'Ligue': league, 'Favori': 'N/A', 'Confiance_Initiale': 'N/A', 'GO_Etape1': False, 'GO_Etape2': False, 'GO_Etape3': False, 'Type_Pari': 'Value Bet', 'Palier_Snowball': 'N/A'})
                    matchs_list.append(row)
            time.sleep(1.2)
        except: continue
    return pd.DataFrame(matchs_list)

# ==========================================
# ⚙️ GESTION SESSIONS
# ==========================================
if 'all_sessions' not in st.session_state:
    st.session_state.all_sessions = {}

with st.sidebar:
    st.header("⚙️ Paramètres")
    session_active = st.selectbox("Session active :", ["Week-end en cours", "Week-end prochain", "Archives"])
    if session_active not in st.session_state.all_sessions or st.session_state.all_sessions[session_active].empty:
        st.session_state.all_sessions[session_active] = pd.DataFrame(columns=ALL_COLS)
    
    st.divider()
    if st.button("🔄 Basculer Prochain ➔ En Cours"):
        st.session_state.all_sessions["Archives"] = st.session_state.all_sessions["Week-end en cours"].copy()
        st.session_state.all_sessions["Week-end en cours"] = st.session_state.all_sessions["Week-end prochain"].copy()
        st.session_state.all_sessions["Week-end prochain"] = pd.DataFrame(columns=ALL_COLS)
        st.rerun()

# ==========================================
    # 💾 SAUVEGARDE & SYNCHRO
    # ==========================================
    st.divider()
    st.subheader("💾 Sauvegarde & Synchro")
    
    # Bouton d'exportation
    export_dict = {k: v.to_dict(orient="records") for k, v in st.session_state.all_sessions.items()}
    json_data = json.dumps(export_dict)
    
    st.download_button(
        label="⬇️ Exporter ma War Room",
        data=json_data,
        file_name=f"war_room_save_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json",
        use_container_width=True
    )
    
    # Bouton d'importation
    uploaded_file = st.file_uploader("⬆️ Importer une sauvegarde", type="json")
    if uploaded_file is not None:
        if st.button("Restaurer les données", use_container_width=True):
            imported_data = json.load(uploaded_file)
            for k, v in imported_data.items():
                st.session_state.all_sessions[k] = pd.DataFrame(v)
            st.success("✅ War Room restaurée !")
            st.rerun()

# ==========================================
# 🏗️ INTERFACE
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📡 Radar", "📊 Stats", "🏥 Infirmerie", "💰 Cotes", "🏆 Verdict"])

# --- 1. RADAR ---
with tab1:
    st.header(f"Radar : {session_active}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🚀 LANCER LE SUPER SCANNER"):
            new_df = run_super_scanner(session_active)
            if not new_df.empty: st.session_state.all_sessions[session_active] = new_df.sort_values(by=['Date', 'Heure']); st.rerun()
    with c2:
        if st.button("🗑️ Vider Radar"): st.session_state.all_sessions[session_active] = pd.DataFrame(columns=ALL_COLS); st.rerun()

    df_radar = st.session_state.all_sessions[session_active]
    if not df_radar.empty:
        edited = st.data_editor(df_radar[['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1']], use_container_width=True, hide_index=True, height=600)
        if st.button("💾 Sauvegarder Radar"): st.session_state.all_sessions[session_active].update(edited); st.success("Enregistré !")

# --- 2. STATS (DUEL) ---
with tab2:
    cur_df = st.session_state.all_sessions[session_active]
    matches = cur_df[cur_df['GO_Etape1'] == True] if not cur_df.empty else pd.DataFrame()
    if matches.empty: st.info("Cochez GO au Radar.")
    else:
        for idx, row in matches.iterrows():
            with st.expander(f"⚔️ {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                labels = ["1X2 (%)", "AH (%)", "Over (%)", "1stG (%)", "BTTS (%)", "---", "RTP", "RTA", "Att.D", "Tirs", "Cadrés", "Hors C."]
                df_d = pd.DataFrame({"Indicateur": labels, dom: [row['H_1x2'], row['H_AH'], row['H_Over'], row['H_1stGoal'], row['H_BTTS'], "", row['H_RTP'], row['H_RTA'], row['H_AttD'], row['H_Shots'], row['H_TirC'], row['H_TirH']], ext: [row['A_1x2'], row['A_AH'], row['A_Over'], row['A_1stGoal'], row['A_BTTS'], "", row['A_RTP'], row['A_RTA'], row['A_AttD'], row['A_Shots'], row['A_TirC'], row['A_TirH']]})
                edited_d = st.data_editor(df_d, key=f"d_{idx}", use_container_width=True, height=500)
                if st.button(f"💾 Valider Stats {row['Match']}", key=f"s_{idx}"):
                    st.session_state.all_sessions[session_active].at[idx, 'GO_Etape2'] = True; st.rerun()

# --- 3. INFIRMERIE --- (Inchangé)
with tab3:
    if st.button("🔄 Charger Mémoire"):
        source = "Week-end en cours" if session_active == "Week-end prochain" else "Archives"
        if source in st.session_state.all_sessions:
            old = st.session_state.all_sessions[source]
            st.session_state['memo'] = {p['Joueur']: p for _, r in old.iterrows() for side in ['Absents_Dom', 'Absents_Ext'] if isinstance(r[side], list) for p in r[side] if p.get('Durée') == "Out"}
            st.success("Mémoire chargée.")
    cur_inf = st.session_state.all_sessions[session_active]
    df_inf = cur_inf[cur_inf['GO_Etape2'] == True] if not cur_inf.empty else pd.DataFrame()
    if df_inf.empty: st.info("Validez l'étape 2.")
    else:
        for idx, row in df_inf.iterrows():
            with st.expander(f"🏥 {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                l_dom, l_ext = sorted(players_db.get(dom, [])), sorted(players_db.get(ext, []))
                i_dom = [st.session_state['memo'][p] for p in l_dom if 'memo' in st.session_state and p in st.session_state['memo']]
                i_ext = [st.session_state['memo'][p] for p in l_ext if 'memo' in st.session_state and p in st.session_state['memo']]
                c_d, c_e = st.columns(2)
                with c_d: res_d = st.data_editor(pd.DataFrame(i_dom if i_dom else [], columns=['Joueur', 'Type', 'Durée']), key=f"ad_{idx}", num_rows="dynamic", use_container_width=True, column_config={"Joueur": st.column_config.SelectboxColumn("Joueur", options=l_dom), "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"]), "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"])})
                with c_e: res_e = st.data_editor(pd.DataFrame(i_ext if i_ext else [], columns=['Joueur', 'Type', 'Durée']), key=f"ae_{idx}", num_rows="dynamic", use_container_width=True, column_config={"Joueur": st.column_config.SelectboxColumn("Joueur", options=l_ext), "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"]), "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"])})
                if st.checkbox(f"Valider Infirmerie {row['Match']}", key=f"v_{idx}"):
                    st.session_state.all_sessions[session_active].at[idx, 'GO_Etape3'] = True
                    st.session_state.all_sessions[session_active].at[idx, 'Absents_Dom'], st.session_state.all_sessions[session_active].at[idx, 'Absents_Ext'] = res_d.to_dict('records'), res_e.to_dict('records')

# --- 4. COTES ---
with tab4:
    st.header(f"Cotes Scooore : {session_active}")
    cur_cotes = st.session_state.all_sessions[session_active]
    df_cotes = cur_cotes[cur_cotes['GO_Etape3'] == True] if not cur_cotes.empty else pd.DataFrame()
    if df_cotes.empty: st.info("Validez l'étape 3 (Infirmerie).")
    else:
        for idx, row in df_cotes.iterrows():
            with st.expander(f"💰 {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                c1, c2, c3 = st.columns(3)
                with c1: st.data_editor(pd.DataFrame({"Marché": ["1","X","2","DNB 1","DNB 2","1X","X2"], "Cote": [1.0]*7}), key=f"c1_{idx}", hide_index=True)
                with c2: st.data_editor(pd.DataFrame({"Marché": ["BTTS Oui","BTTS Non","Over 1.5","Over 2.5","Over 3.5","Under 1.5","Under 2.5","Under 3.5"], "Cote": [1.0]*8}), key=f"c2_{idx}", hide_index=True)
                with c3: st.data_editor(pd.DataFrame({"Hdc": ["-1.5","-0.5","0.5","1.5"], "Cote Dom": [1.0]*4, "Cote Ext": [1.0]*4}), key=f"c3_{idx}", hide_index=True)

# --- 5. VERDICT ---
with tab5:
    st.header(f"Verdict Final : {session_active}")
    df_v = st.session_state.all_sessions[session_active]
    
    # Sécurité : On vérifie que le DataFrame n'est pas vide et contient bien GO_Etape1
    if not df_v.empty and 'GO_Etape1' in df_v.columns:
        df_final = df_v[df_v['GO_Etape1'] == True]
        
        if df_final.empty: 
            st.info("Cochez des matchs au Radar pour les voir apparaître ici.")
        else:
            # Correction de la configuration des colonnes (Retrait du placeholder problématique)
            edited_v = st.data_editor(
                df_final[['Date', 'Heure', 'Match', 'Confiance_Initiale', 'Conf_AIStats', 'Conf_FotMob', 'Type_Pari', 'Palier_Snowball', 'Meteo', 'Arbitre', 'Pari_Final']],
                column_config={
                    "Type_Pari": st.column_config.SelectboxColumn("Type", options=["Value Bet", "Snowball"], required=True),
                    "Palier_Snowball": st.column_config.SelectboxColumn("Palier", options=["N/A", "1", "2", "3", "4", "5", "Bonus"]),
                    "Meteo": st.column_config.SelectboxColumn("Météo", options=["Beau temps", "Pluie", "Vent fort", "Froid intense", "Neige"]),
                    "Arbitre": st.column_config.SelectboxColumn("Arbitre", options=ALL_REFEREES),
                    "Pari_Final": st.column_config.TextColumn("Pari Final") # Simplifié ici
                },
                use_container_width=True, 
                hide_index=True, 
                height=600, 
                key=f"ved_final_{session_active}"
            )
            
            if st.button("💾 Sauvegarder Verdict", key="save_verdict_btn"):
                st.session_state.all_sessions[session_active].update(edited_v)
                st.success("Données sauvegardées avec succès !")

            st.divider()
            # Génération des prompts pour les matchs sélectionnés
            for idx, row in df_final.iterrows():
                if st.button(f"📰 Générer Prompt : {row['Match']}", key=f"pb_final_{idx}"):
                    p = f"### ANALYSE SNIPER : {row['Match']} ###\n"
                    p += f"Confiances : Init({row['Confiance_Initiale']}) | AI({row['Conf_AIStats']}) | FotMob({row['Conf_FotMob']})\n"
                    p += f"Stratégie : {row['Type_Pari']} (Palier: {row['Palier_Snowball']})\n"
                    p += f"Contexte : Météo {row['Meteo']} | Arbitre: {row['Arbitre']}\n"
                    p += f"Absents : {row['Absents_Dom']} / {row['Absents_Ext']}\n"
                    p += "Donne-moi ton verdict final basé sur la revue de presse locale et les enjeux du club."
                    st.code(p)
    else:
        st.info("Lancez un scan et sélectionnez des matchs au Radar.")
