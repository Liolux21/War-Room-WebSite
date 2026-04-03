import streamlit as st
import pandas as pd

# Configuration
st.set_page_config(page_title="War Room - Sniper Dashboard", layout="wide")
st.title("🎯 War Room - Pipeline d'Analyse")

# 1. Initialisation étendue du Master DF
if 'master_df' not in st.session_state:
    # On définit toutes les colonnes nécessaires pour le stockage
    stats_cols = [
        'H_1x2', 'A_1x2', 'H_AH', 'A_AH', 'H_Over', 'A_Over', 'H_1stGoal', 'A_1stGoal', 'H_BTTS', 'A_BTTS',
        'H_RTP', 'A_RTP', 'H_RTA', 'A_RTA', 'H_AttD', 'A_AttD', 'H_Shots', 'A_Shots', 'H_TirC', 'A_TirC', 'H_TirH', 'A_TirH'
    ]
    base_cols = ['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1', 'GO_Etape2', 'GO_Etape3', 'Absents_Dom', 'Absents_Ext', 'Cote_Cible', 'Pari_Final']
    st.session_state.master_df = pd.DataFrame(columns=base_cols + stats_cols)
    
    # Donnée Test
    st.session_state.master_df.loc[0, ['Date', 'Match', 'Ligue', 'GO_Etape1']] = ['2026-04-06', 'Udinese vs Como', 'Serie A', True]

# Onglets
tab1, tab2, tab3, tab4 = st.tabs(["📡 Radar", "📊 Stats (Duel)", "🏥 Infirmerie", "🧮 Verdict"])

# --- ONGLET 1 : RADAR ---
with tab1:
    st.header("1. Sélection initiale")
    edited_radar = st.data_editor(st.session_state.master_df[['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'GO_Etape1']], use_container_width=True, hide_index=True)
    st.session_state.master_df.update(edited_radar)
    
    if st.button("🤖 Envoyer le Radar à l'IA"):
        matches = st.session_state.master_df[st.session_state.master_df['GO_Etape1'] == True]['Match'].tolist()
        st.code(f"Radar Validé. Matchs à analyser en profondeur : {matches}", language="text")

# --- ONGLET 2 : SALLE DES MACHINES (LA MODIFICATION DEMANDÉE) ---
with tab2:
    st.header("2. Saisie AIStats (Duel)")
    matches_to_analyze = st.session_state.master_df[st.session_state.master_df['GO_Etape1'] == True]
    
    if matches_to_analyze.empty:
        st.warning("Aucun match sélectionné au Radar.")
    else:
        for idx, row in matches_to_analyze.iterrows():
            with st.expander(f"⚔️ {row['Match']}", expanded=True):
                # Définition des labels
                labels = [
                    "1X2 (%)", "Handicap Asiatique (%)", "Total Plus (%)", "Premier but (%)", "BTTS (%)",
                    "---", 
                    "RTP", "RTA", "Attaques dangereuses", "Total des tirs", "Tirs cadrés", "Tirs hors cadre"
                ]
                
                # On prépare le DataFrame vertical pour l'éditeur
                dom, ext = row['Match'].split(' vs ')
                data = {
                    "Indicateur": labels,
                    dom: [row['H_1x2'], row['H_AH'], row['H_Over'], row['H_1stGoal'], row['H_BTTS'], "", row['H_RTP'], row['H_RTA'], row['H_AttD'], row['H_Shots'], row['H_TirC'], row['H_TirH']],
                    ext: [row['A_1x2'], row['A_AH'], row['A_Over'], row['A_1stGoal'], row['A_BTTS'], "", row['A_RTP'], row['A_RTA'], row['A_AttD'], row['A_Shots'], row['A_TirC'], row['A_TirH']]
                }
                df_duel = pd.DataFrame(data)
                
                # Éditeur de tableau vertical
                edited_duel = st.data_editor(df_duel, key=f"editor_{idx}", use_container_width=True, hide_index=True)
                
                # Bouton de sauvegarde locale pour ce match
                if st.button(f"💾 Sauvegarder Stats {row['Match']}", key=f"btn_{idx}"):
                    # On repousse les données dans le master_df
                    st.session_state.master_df.at[idx, 'H_1x2'] = edited_duel.iloc[0, 1]
                    st.session_state.master_df.at[idx, 'A_1x2'] = edited_duel.iloc[0, 2]
                    # ... (on pourrait automatiser le mapping ici)
                    st.session_state.master_df.at[idx, 'GO_Etape2'] = True
                    st.success("Stats enregistrées !")

        st.divider()
        if st.button("🤖 Envoyer Stats à l'IA pour calcul d'indice"):
            valid_stats = st.session_state.master_df[st.session_state.master_df['GO_Etape2'] == True]
            st.code(f"Voici les stats AIStats pour analyse :\n{valid_stats.to_string()}", language="text")

# --- ONGLET 3 : INFIRMERIE ---
with tab3:
    st.header("3. État des troupes")
    df_inf = st.session_state.master_df[st.session_state.master_df['GO_Etape2'] == True]
    if not df_inf.empty:
        edited_inf = st.data_editor(df_inf[['Match', 'Absents_Dom', 'Absents_Ext', 'GO_Etape3']], use_container_width=True, hide_index=True)
        st.session_state.master_df.update(edited_inf)
        
        if st.button("🤖 Envoyer l'Infirmerie à l'IA"):
            st.code(f"Analyse des absents demandée pour :\n{edited_inf.to_string()}", language="text")
    else:
        st.info("Validez l'étape 2 d'abord.")

# --- ONGLET 4 : VERDICT ---
with tab4:
    st.header("4. Cotes & Revue de Presse")
    df_final = st.session_state.master_df[st.session_state.master_df['GO_Etape3'] == True]
    if not df_final.empty:
        edited_final = st.data_editor(df_final[['Match', 'Cote_Cible', 'Pari_Final']], use_container_width=True, hide_index=True)
        st.session_state.master_df.update(edited_final)
        
        if st.button("📰 Générer demande Revue de Presse"):
            st.code(f"Fais-moi la revue de presse pour : {df_final['Match'].tolist()}", language="text")
