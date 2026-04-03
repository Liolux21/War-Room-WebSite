import streamlit as st
import pandas as pd
import os

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(page_title="War Room - Sniper Dashboard", layout="wide")

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

# ==========================================
# ONGLET 3 : INFIRMERIE (EFFECTIFS DB)
# ==========================================
with tab3:
    st.header("3. Infirmerie & Disponibilité")
    df_inf = st.session_state.master_df[st.session_state.master_df['GO_Etape2'] == True]
    
    if df_inf.empty:
        st.info("Validez l'étape 2 pour charger les effectifs.")
    else:
        for idx, row in df_inf.iterrows():
            with st.expander(f"🏥 Effectifs : {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                
                # Récupération des listes de joueurs depuis MASTER_ANALYSE
                list_players_dom = sorted(players_db.get(dom, []))
                list_players_ext = sorted(players_db.get(ext, []))

                col_dom, col_ext = st.columns(2)
                
                with col_dom:
                    st.subheader(f"🏠 {dom}")
                    df_abs_dom = st.data_editor(
                        pd.DataFrame(columns=['Joueur', 'Type', 'Durée']),
                        key=f"abs_dom_ed_{idx}", num_rows="dynamic", use_container_width=True,
                        column_config={
                            "Joueur": st.column_config.SelectboxColumn("Joueur", options=list_players_dom, required=True),
                            "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"], required=True),
                            "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"], required=True)
                        }
                    )
                    df_abs_dom.loc[df_abs_dom['Type'] == "Suspendu", "Durée"] = "Out"

                with col_ext:
                    st.subheader(f"🚀 {ext}")
                    df_abs_ext = st.data_editor(
                        pd.DataFrame(columns=['Joueur', 'Type', 'Durée']),
                        key=f"abs_ext_ed_{idx}", num_rows="dynamic", use_container_width=True,
                        column_config={
                            "Joueur": st.column_config.SelectboxColumn("Joueur", options=list_players_ext, required=True),
                            "Type": st.column_config.SelectboxColumn("Type", options=["Blessé", "Malade", "Suspendu"], required=True),
                            "Durée": st.column_config.SelectboxColumn("Durée", options=["Incertain", "Out"], required=True)
                        }
                    )
                    df_abs_ext.loc[df_abs_ext['Type'] == "Suspendu", "Durée"] = "Out"

                if st.checkbox(f"Valider impact effectif pour {row['Match']}", key=f"val_inf_{idx}"):
                    st.session_state.master_df.at[idx, 'GO_Etape3'] = True
                    st.session_state.master_df.at[idx, 'Absents_Dom'] = df_abs_dom.to_dict('records')
                    st.session_state.master_df.at[idx, 'Absents_Ext'] = df_abs_ext.to_dict('records')

        if st.button("🤖 Envoyer l'Infirmerie à l'IA"):
            prompt_inf = "Voici l'état des effectifs. L'asymétrie est-elle confirmée ?\n"
            for _, r in st.session_state.master_df[st.session_state.master_df['GO_Etape3'] == True].iterrows():
                prompt_inf += f"\n- {r['Match']} :\n  DOM: {r['Absents_Dom']}\n  EXT: {r['Absents_Ext']}\n"
            st.code(prompt_inf, language="text")

# ==========================================
# ONGLET 4 : VERDICT FINAL
# ==========================================
with tab4:
    st.header("4. Cotes & Revue de Presse")
    df_final = st.session_state.master_df[st.session_state.master_df['GO_Etape3'] == True]
    
    if df_final.empty:
        st.warning("Aucun match n'a survécu à l'entonnoir.")
    else:
        edited_final = st.data_editor(df_final[['Match', 'Cote_Cible', 'Pari_Final']], use_container_width=True, hide_index=True, key="final_ed")
        
        if st.button("📰 Générer demande Revue de Presse Finale"):
            for m in df_final['Match'].tolist():
                st.write(f"--- Rapport pour {m} ---")
                p = f"Fais-moi l'analyse approfondie (Onze, Tactique, Climat, Verdict) pour {m}. \nDonnées : {st.session_state.master_df[st.session_state.master_df['Match'] == m].to_dict('records')}"
                st.code(p, language="text")
