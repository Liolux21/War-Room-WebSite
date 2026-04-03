import streamlit as st
import pandas as pd
import os

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="War Room - Sniper Dashboard", layout="wide")

# 2. CHARGEMENT DE LA BASE DE DONNÉES DES JOUEURS (Effectifs)
@st.cache_data
def load_players_db():
    file_name = "MASTER_ANALYSE_2026-04-02.csv"
    try:
        if os.path.exists(file_name):
            df = pd.read_csv(file_name)
            return df.groupby('Equipe')['Joueur'].apply(list).to_dict()
        else:
            return {}
    except Exception as e:
        return {}

players_db = load_players_db()

# 3. GESTION DES SESSIONS (Sidebar)
with st.sidebar:
    st.header("⚙️ Paramètres")
    session_active = st.selectbox(
        "Session de travail :",
        ["Week-end en cours", "Week-end prochain", "Archives"],
        index=0
    )
    st.info(f"📍 Mode : **{session_active}**")

# Initialisation du dictionnaire de sessions dans le State
if 'all_sessions' not in st.session_state:
    st.session_state.all_sessions = {}

# Structure de base si la session est nouvelle
if session_active not in st.session_state.all_sessions:
    stats_cols = [
        'H_1x2', 'A_1x2', 'H_AH', 'A_AH', 'H_Over', 'A_Over', 'H_1stGoal', 'A_1stGoal', 'H_BTTS', 'A_BTTS',
        'H_RTP', 'A_RTP', 'H_RTA', 'A_RTA', 'H_AttD', 'A_AttD', 'H_Shots', 'A_Shots', 'H_TirC', 'A_TirC', 'H_TirH', 'A_TirH'
    ]
    base_cols = ['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1', 'GO_Etape2', 'GO_Etape3', 'Absents_Dom', 'Absents_Ext', 'Cote_Cible', 'Pari_Final']
    st.session_state.all_sessions[session_active] = pd.DataFrame(columns=base_cols + stats_cols)

# 4. INTERFACE PAR ONGLETS
st.title("🎯 War Room - Betting Pipeline")
tab1, tab2, tab3, tab4 = st.tabs(["📡 Radar", "📊 Stats (Duel)", "🏥 Infirmerie", "🧮 Verdict Final"])

# ==========================================
# ONGLET 1 : RADAR
# ==========================================
with tab1:
    st.header(f"1. Sélection Radar : {session_active}")
    cols_radar = ['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1']
    
    # On récupère le DF de la session
    df_radar = st.session_state.all_sessions[session_active]
    
    edited_radar = st.data_editor(df_radar[cols_radar], use_container_width=True, hide_index=True, key=f"radar_{session_active}", num_rows="dynamic")
    
    if st.button("💾 Sauvegarder la sélection Radar", key=f"save_radar_{session_active}"):
        # On fusionne les modifs dans la session (en gérant les nouvelles lignes)
        st.session_state.all_sessions[session_active].update(edited_radar)
        st.success("Radar mis à jour !")

# ==========================================
# ONGLET 2 : SALLE DES MACHINES
# ==========================================
with tab2:
    st.header(f"2. Saisie AIStats : {session_active}")
    current_df = st.session_state.all_sessions[session_active]
    matches_to_analyze = current_df[current_df['GO_Etape1'] == True]
    
    if matches_to_analyze.empty:
        st.warning("Aucun match sélectionné au Radar.")
    else:
        for idx, row in matches_to_analyze.iterrows():
            with st.expander(f"⚔️ {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                labels = ["1X2 (%)", "Handicap Asiatique (%)", "Total Plus (%)", "Premier but (%)", "BTTS (%)", "---", "RTP", "RTA", "Attaques dangereuses", "Total des tirs", "Tirs cadrés", "Tirs hors cadre"]
                
                data_duel = {
                    "Indicateur": labels,
                    dom: [row['H_1x2'], row['H_AH'], row['H_Over'], row['H_1stGoal'], row['H_BTTS'], "", row['H_RTP'], row['H_RTA'], row['H_AttD'], row['H_Shots'], row['H_TirC'], row['H_TirH']],
                    ext: [row['A_1x2'], row['A_AH'], row['A_Over'], row['A_1stGoal'], row['A_BTTS'], "", row['A_RTP'], row['A_RTA'], row['A_AttD'], row['A_Shots'], row['A_TirC'], row['A_TirH']]
                }
                
                df_duel = pd.DataFrame(data_duel)
                edited_duel = st.data_editor(df_duel, key=f"duel_{session_active}_{idx}", use_container_width=True, hide_index=True)
                
                if st.button(f"💾 Valider Stats : {row['Match']}", key=f"save_btn_{session_active}_{idx}"):
                    # Enregistrement forcé
                    st.session_state.all_sessions[session_active].at[idx, 'H_1x2'] = edited_duel.iloc[0, 1]
                    st.session_state.all_sessions[session_active].at[idx, 'A_1x2'] = edited_duel.iloc[0, 2]
                    st.session_state.all_sessions[session_active].at[idx, 'GO_Etape2'] = True
                    st.success(f"✅ Stats validées pour {row['Match']}.")
                    st.rerun()

# ==========================================
# ONGLET 3 : INFIRMERIE (AVEC MÉMOIRE)
# ==========================================
with tab3:
    st.header(f"3. État des troupes : {session_active}")
    
    # Bouton Mémoire
    if st.button("🔄 Récupérer les blessés (Session précédente)"):
        source = "Week-end en cours" if session_active == "Week-end prochain" else "Archives"
        if source in st.session_state.all_sessions:
            old_data = st.session_state.all_sessions[source]
            memo = {}
            for _, r in old_data.iterrows():
                for side in ['Absents_Dom', 'Absents_Ext']:
                    if isinstance(r[side], list):
                        for p in r[side]:
                            if p.get('Durée') == "Out": memo[p['Joueur']] = p
            st.session_state['memo_absents'] = memo
            st.success("Mémoire chargée !")

    current_df_inf = st.session_state.all_sessions[session_active]
    df_ready = current_df_inf[current_df_inf['GO_Etape2'] == True]
    
    if df_ready.empty:
        st.info("💡 Validez l'étape 2 (Stats) pour débloquer cet onglet.")
    else:
        for idx, row in df_ready.iterrows():
            with st.expander(f"🏥 Effectifs : {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                list_players_dom = sorted(players_db.get(dom, []))
                list_players_ext = sorted(players_db.get(ext, []))

                # Pré-remplissage mémoire
                init_dom = [st.session_state['memo_absents'][p] for p in list_players_dom if 'memo_absents' in st.session_state and p in st.session_state['memo_absents']]
                init_ext = [st.session_state['memo_absents'][p] for p in list_players_ext if 'memo_absents' in st.session_state and p in st.session_state['memo_absents']]

                col_dom, col_ext = st.columns(2)
                with col_dom:
                    st.subheader(f"🏠 {dom}")
                    df_abs_dom = st.data_editor(pd.DataFrame(init_dom if init_dom else [], columns=['Joueur', 'Type', 'Durée']),
                        key=f"abs_dom_{session_active}_{idx}", num_rows="dynamic", use_container_width=True,
                        column_config={
                            "Joueur": st.column_config.SelectboxColumn("Joueur", options=list_players_dom, required=True),
                            "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"]),
                            "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"])
                        })
                with col_ext:
                    st.subheader(f"🚀 {ext}")
                    df_abs_ext = st.data_editor(pd.DataFrame(init_ext if init_ext else [], columns=['Joueur', 'Type', 'Durée']),
                        key=f"abs_ext_{session_active}_{idx}", num_rows="dynamic", use_container_width=True,
                        column_config={
                            "Joueur": st.column_config.SelectboxColumn("Joueur", options=list_players_ext, required=True),
                            "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"]),
                            "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"])
                        })

                if st.checkbox(f"Valider impact : {row['Match']}", key=f"val_inf_{session_active}_{idx}"):
                    st.session_state.all_sessions[session_active].at[idx, 'GO_Etape3'] = True
                    st.session_state.all_sessions[session_active].at[idx, 'Absents_Dom'] = df_abs_dom.to_dict('records')
                    st.session_state.all_sessions[session_active].at[idx, 'Absents_Ext'] = df_abs_ext.to_dict('records')

# ==========================================
# ONGLET 4 : VERDICT & COTES
# ==========================================
with tab4:
    st.header(f"4. Cotes Scooore : {session_active}")
    df_final = st.session_state.all_sessions[session_active][st.session_state.all_sessions[session_active]['GO_Etape3'] == True]
    
    if df_final.empty:
        st.warning("Aucun match n'a survécu à l'entonnoir.")
    else:
        for idx, row in df_final.iterrows():
            with st.expander(f"💰 {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.data_editor(pd.DataFrame({"Marché": ["1","X","2","DNB 1","DNB 2","1X","X2"], "Cote": [1.0]*7}), key=f"c1_{idx}", hide_index=True)
                with c2:
                    st.data_editor(pd.DataFrame({"Marché": ["BTTS Oui","BTTS Non","Over 1.5","Over 2.5","Over 3.5","Under 1.5","Under 2.5","Under 3.5"], "Cote": [1.0]*8}), key=f"c2_{idx}", hide_index=True)
                with c3:
                    st.data_editor(pd.DataFrame({f"Hdc {dom}": ["-0.5","+0.5"], "Cote Dom": [1.0, 1.0], f"Hdc {ext}": ["-0.5","+0.5"], "Cote Ext": [1.0, 1.0]}), key=f"c3_{idx}", hide_index=True)
                
                if st.button(f"📰 Prompt Revue de Presse : {row['Match']}", key=f"prompt_{idx}"):
                    p = f"Analyse approfondie pour {row['Match']}. Absents validés : {row['Absents_Dom']} / {row['Absents_Ext']}."
                    st.code(p)
