import streamlit as st
import pandas as pd
import os

# 1. SÉLECTEUR DE SESSION (Tout en haut du script)
with st.sidebar:
    st.header("⚙️ Paramètres")
    session_active = st.selectbox(
        "Session de travail :",
        ["Week-end en cours", "Week-end prochain", "Archives"],
        index=0
    )
    st.info(f"📍 Vous travaillez sur : **{session_active}**")

# 2. INITIALISATION MULTI-SESSION
if 'all_sessions' not in st.session_state:
    st.session_state.all_sessions = {}

# Si la session sélectionnée n'existe pas encore, on la crée proprement
if session_active not in st.session_state.all_sessions:
    # On définit la structure vide pour cette session précise
    stats_cols = [
        'H_1x2', 'A_1x2', 'H_AH', 'A_AH', 'H_Over', 'A_Over', 'H_1stGoal', 'A_1stGoal', 'H_BTTS', 'A_BTTS',
        'H_RTP', 'A_RTP', 'H_RTA', 'A_RTA', 'H_AttD', 'A_AttD', 'H_Shots', 'A_Shots', 'H_TirC', 'A_TirC', 'H_TirH', 'A_TirH'
    ]
    base_cols = ['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1', 'GO_Etape2', 'GO_Etape3', 'Absents_Dom', 'Absents_Ext', 'Cote_Cible', 'Pari_Final']
    
    # Création du DataFrame pour CETTE session
    st.session_state.all_sessions[session_active] = pd.DataFrame(columns=base_cols + stats_cols)

# RACCOURCI : On définit 'master_df' comme étant la session active pour ne pas casser le reste du code
master_df = st.session_state.all_sessions[session_active]

# 2. CHARGEMENT DE LA BASE DE DONNÉES DES JOUEURS (Effectifs)
@st.cache_data
def load_players_db():
    try:
        # Lecture du fichier CSV pour extraire les joueurs par équipe
        base_path = os.path.dirname(__file__) # Trouve le dossier où est le script
        file_path = os.path.join(base_path, "MASTER_ANALYSE_2026-04-02.csv")
        df = pd.read_csv(file_path)
        # Création d'un dictionnaire { 'Equipe': [Liste des Joueurs] }
        players_db = df.groupby('Equipe')['Joueur'].apply(list).to_dict()
        return players_db
    except Exception as e:
        st.error(f"Erreur de chargement du fichier MASTER_ANALYSE : {e}")
        return {}

players_db = load_players_db()

# 3. INITIALISATION DU SESSION STATE (Base de données locale de l'app)
if 'master_df' not in st.session_state:
    # Liste de toutes les colonnes de stockage
    stats_cols = [
        'H_1x2', 'A_1x2', 'H_AH', 'A_AH', 'H_Over', 'A_Over', 'H_1stGoal', 'A_1stGoal', 'H_BTTS', 'A_BTTS',
        'H_RTP', 'A_RTP', 'H_RTA', 'A_RTA', 'H_AttD', 'A_AttD', 'H_Shots', 'A_Shots', 'H_TirC', 'A_TirC', 'H_TirH', 'A_TirH'
    ]
    base_cols = ['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1', 'GO_Etape2', 'GO_Etape3', 'Absents_Dom', 'Absents_Ext', 'Cote_Cible', 'Pari_Final']
    
    st.session_state.master_df = pd.DataFrame(columns=base_cols + stats_cols)
    
    # Ligne d'exemple pour tester l'interface
    st.session_state.master_df.loc[0, ['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1']] = \
        ['2026-04-06', '12:30', 'Udinese vs Como', 'Serie A', 'Como', '75%', True]

# Fonction de mise à jour globale
def update_master():
    pass # La mise à jour se fait via les clés st.session_state

# 4. INTERFACE PAR ONGLETS
st.title("🎯 War Room - Betting Pipeline")
tab1, tab2, tab3, tab4 = st.tabs(["📡 Radar (Import)", "📊 Stats (Duel)", "🏥 Infirmerie", "🧮 Verdict Final"])

# ==========================================
# ONGLET 1 : LE RADAR
# ==========================================
with tab1:
    st.header("1. Sélection du Calendrier")
    cols_radar = ['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1']
    edited_radar = st.data_editor(st.session_state.master_df[cols_radar], use_container_width=True, hide_index=True, key="radar_editor")
    
    if st.button("💾 Sauvegarder la sélection Radar"):
        st.session_state.master_df.update(edited_radar)
        st.success("Radar mis à jour !")

    if st.button("🤖 Envoyer le Radar à l'IA"):
        matches = st.session_state.master_df[st.session_state.master_df['GO_Etape1'] == True]['Match'].tolist()
        st.code(f"Matchs sélectionnés pour analyse approfondie : {matches}", language="text")

# ==========================================
# ONGLET 2 : SALLE DES MACHINES (DUEL)
# ==========================================
with tab2:
    st.header("2. Saisie AIStats (Comparaison Directe)")
    matches_to_analyze = st.session_state.master_df[st.session_state.master_df['GO_Etape1'] == True]
    
    if matches_to_analyze.empty:
        st.warning("Aucun match sélectionné dans l'onglet Radar.")
    else:
        for idx, row in matches_to_analyze.iterrows():
            with st.expander(f"⚔️ {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                
                # Labels demandés
                labels = [
                    "1X2 (%)", "Handicap Asiatique (%)", "Total Plus (%)", "Premier but (%)", "BTTS (%)",
                    "---", 
                    "RTP", "RTA", "Attaques dangereuses", "Total des tirs", "Tirs cadrés", "Tirs hors cadre"
                ]
                
                # Construction du tableau vertical
                data_duel = {
                    "Indicateur": labels,
                    dom: [row['H_1x2'], row['H_AH'], row['H_Over'], row['H_1stGoal'], row['H_BTTS'], "", row['H_RTP'], row['H_RTA'], row['H_AttD'], row['H_Shots'], row['H_TirC'], row['H_TirH']],
                    ext: [row['A_1x2'], row['A_AH'], row['A_Over'], row['A_1stGoal'], row['A_BTTS'], "", row['A_RTP'], row['A_RTA'], row['A_AttD'], row['A_Shots'], row['A_TirC'], row['A_TirH']]
                }
                df_duel = pd.DataFrame(data_duel)
                
                edited_duel = st.data_editor(df_duel, key=f"duel_{idx}", use_container_width=True, hide_index=True)
                
                if st.button(f"💾 Sauvegarder Stats : {row['Match']}", key=f"save_stats_{idx}"):
                    # Mapping manuel des lignes vers le master_df
                    st.session_state.master_df.at[idx, 'H_1x2'] = edited_duel.iloc[0, 1]
                    st.session_state.master_df.at[idx, 'A_1x2'] = edited_duel.iloc[0, 2]
                    st.session_state.master_df.at[idx, 'H_RTP'] = edited_duel.iloc[6, 1]
                    st.session_state.master_df.at[idx, 'A_RTP'] = edited_duel.iloc[6, 2]
                    # On valide le passage à l'étape suivante
                    st.session_state.master_df.at[idx, 'GO_Etape2'] = True
                    st.success(f"Stats enregistrées pour {row['Match']}")

        if st.button("🤖 Envoyer Stats à l'IA"):
            valid_stats = st.session_state.master_df[st.session_state.master_df['GO_Etape2'] == True]
            st.code(f"Stats AIStats pour calcul de Value :\n{valid_stats.to_string()}", language="text")

# --- ONGLET 3 : L'INFIRMERIE (VERSION AVEC MÉMOIRE) ---
with tab3:
    st.header(f"3. État des troupes ({session_active})")
    
    # 1. BOUTON DE RÉCUPÉRATION (Mémoire)
    col_mem, col_empty = st.columns([1, 2])
    with col_mem:
        if st.button("🔄 Récupérer les blessés (Session Précédente)"):
            # On définit la session source (si on est sur 'prochain', on regarde 'en cours')
            source_session = "Week-end en cours" if session_active == "Week-end prochain" else "Archives"
            
            if source_session in st.session_state.all_sessions:
                old_data = st.session_state.all_sessions[source_session]
                # On extrait tous les blessés "Out" de la session précédente dans un dictionnaire
                memo_absents = {}
                for _, r in old_data.iterrows():
                    if isinstance(r['Absents_Dom'], list):
                        for p in r['Absents_Dom']:
                            if p['Durée'] == "Out": memo_absents[p['Joueur']] = p
                    if isinstance(r['Absents_Ext'], list):
                        for p in r['Absents_Ext']:
                            if p['Durée'] == "Out": memo_absents[p['Joueur']] = p
                
                st.session_state['memo_absents'] = memo_absents
                st.success(f"Mémoire chargée : {len(memo_absents)} blessés de longue date mémorisés.")
            else:
                st.warning("Aucune donnée source trouvée pour la récupération.")

    # 2. AFFICHAGE DES MATCHS
    df_inf = st.session_state.all_sessions[session_active][st.session_state.all_sessions[session_active]['GO_Etape2'] == True]
    
    if df_inf.empty:
        st.info("Validez l'étape 2 pour accéder aux effectifs.")
    else:
        for idx, row in df_inf.iterrows():
            with st.expander(f"🏥 Effectifs : {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                list_players_dom = sorted(players_db.get(dom, []))
                list_players_ext = sorted(players_db.get(ext, []))

                # On pré-remplit avec la mémoire si elle existe
                initial_dom = []
                initial_ext = []
                if 'memo_absents' in st.session_state:
                    initial_dom = [st.session_state['memo_absents'][p] for p in list_players_dom if p in st.session_state['memo_absents']]
                    initial_ext = [st.session_state['memo_absents'][p] for p in list_players_ext if p in st.session_state['memo_absents']]

                col_dom, col_ext = st.columns(2)
                with col_dom:
                    st.subheader(f"🏠 {dom}")
                    df_abs_dom = st.data_editor(
                        pd.DataFrame(initial_dom if initial_dom else columns=['Joueur', 'Type', 'Durée']),
                        key=f"abs_dom_ed_{session_active}_{idx}", num_rows="dynamic", use_container_width=True,
                        column_config={
                            "Joueur": st.column_config.SelectboxColumn("Joueur", options=list_players_dom, required=True),
                            "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"], required=True),
                            "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"], required=True)
                        }
                    )
                with col_ext:
                    st.subheader(f"🚀 {ext}")
                    df_abs_ext = st.data_editor(
                        pd.DataFrame(initial_ext if initial_ext else columns=['Joueur', 'Type', 'Durée']),
                        key=f"abs_ext_ed_{session_active}_{idx}", num_rows="dynamic", use_container_width=True,
                        column_config={
                            "Joueur": st.column_config.SelectboxColumn("Joueur", options=list_players_ext, required=True),
                            "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"], required=True),
                            "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"], required=True)
                        }
                    )

                if st.checkbox(f"Valider impact effectif : {row['Match']}", key=f"val_inf_{session_active}_{idx}"):
                    st.session_state.all_sessions[session_active].at[idx, 'GO_Etape3'] = True
                    st.session_state.all_sessions[session_active].at[idx, 'Absents_Dom'] = df_abs_dom.to_dict('records')
                    st.session_state.all_sessions[session_active].at[idx, 'Absents_Ext'] = df_abs_ext.to_dict('records')
# ==========================================
# ONGLET 4 : COTES SCOOORE & VERDICT FINAL
# ==========================================
with tab4:
    st.header("4. Cotes Scooore & Analyse de Value")
    
    # On ne garde que les survivants de l'infirmerie
    df_final = st.session_state.master_df[st.session_state.master_df['GO_Etape3'] == True]
    
    if df_final.empty:
        st.warning("Aucun match n'a encore validé l'étape de l'infirmerie.")
    else:
        for idx, row in df_final.iterrows():
            with st.expander(f"💰 Cotes Scooore : {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.subheader("🏆 Issues & DC")
                    df_issues = st.data_editor(
                        pd.DataFrame({
                            "Marché": ["1", "X", "2", "DNB 1", "DNB 2", "1X", "X2"],
                            "Cote": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
                        }), key=f"cotes_issues_{idx}", use_container_width=True, hide_index=True
                    )
                
                with col2:
                    st.subheader("⚽ Totaux & BTTS")
                    df_goals = st.data_editor(
                        pd.DataFrame({
                            "Marché": ["BTTS Oui", "BTTS Non", "Over 1.5", "Over 2.5", "Over 3.5", "Under 1.5", "Under 2.5", "Under 3.5"],
                            "Cote": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
                        }), key=f"cotes_goals_{idx}", use_container_width=True, hide_index=True
                    )
                
                with col3:
                    st.subheader("📉 Handicaps")
                    df_handicap = st.data_editor(
                        pd.DataFrame({
                            f"Hdc {dom}": ["-1.5", "-0.5", "+0.5", "+1.5"],
                            "Cote Dom": [1.0, 1.0, 1.0, 1.0],
                            f"Hdc {ext}": ["-1.5", "-0.5", "+0.5", "+1.5"],
                            "Cote Ext": [1.0, 1.0, 1.0, 1.0]
                        }), key=f"cotes_hdc_{idx}", use_container_width=True, hide_index=True
                    )

                st.divider()
                # Choix du pari final et calcul de Value
                c1, c2 = st.columns(2)
                with c1:
                    pari_choisi = st.selectbox("Pari final retenu", ["1", "X", "2", "DNB 1", "DNB 2", "BTTS", "Over", "Hdc"], key=f"pari_{idx}")
                    cote_retenue = st.number_input("Cote finale Scooore", min_value=1.01, value=1.50, step=0.01, key=f"final_cote_{idx}")
                
                with c2:
                    # Calcul automatique de la probabilité implicite (1/cote)
                    prob_implicite = (1 / cote_retenue) * 100
                    st.metric("Probabilité Implicite", f"{prob_implicite:.1f}%")
                    st.info(f"Compare ce chiffre à ton Indice de Confiance ({row['Confiance_Initiale']}). Si l'Indice > Probabilité, c'est une EV+ !")

                if st.button(f"📰 Revue de Presse Finale : {row['Match']}", key=f"btn_revue_{idx}"):
                    # Compilation de toutes les données saisies pour l'IA
                    prompt = f"### ANALYSE FINALE : {row['Match']} ###\n"
                    prompt += f"Ligue : {row['Ligue']} | Confiance Initiale : {row['Confiance_Initiale']}\n"
                    prompt += f"Pari envisagé : {pari_choisi} à @{cote_retenue}\n"
                    prompt += f"Absents validés : {row['Absents_Dom']} / {row['Absents_Ext']}\n"
                    prompt += "\nPeux-tu scanner la presse locale et les conf' de presse pour ce match ?\n"
                    prompt += "Cherche spécifiquement une rotation surprise pour l'Europe ou une info de vestiaire qui impacterait notre Value."
                    st.code(prompt, language="text")
