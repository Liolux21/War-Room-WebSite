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

# --- ONGLET 3 : L'INFIRMERIE ---
with tab3:
    st.header("3. État des troupes (Détails des absences)")
    
    # On récupère les matchs validés à l'étape 2
    df_inf = st.session_state.master_df[st.session_state.master_df['GO_Etape2'] == True]
    
    if df_inf.empty:
        st.info("Veuillez valider des matchs à l'étape 2 (Stats) pour remplir l'infirmerie.")
    else:
        for idx, row in df_inf.iterrows():
            with st.expander(f"🏥 Infirmerie : {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                
                col_dom, col_ext = st.columns(2)
                
                with col_dom:
                    st.subheader(f"🏠 {dom}")
                    # Configuration du tableau des absents Domicile
                    df_abs_dom = st.data_editor(
                        pd.DataFrame(columns=['Joueur', 'Type', 'Durée']),
                        key=f"abs_dom_{idx}",
                        num_rows="dynamic",
                        use_container_width=True,
                        column_config={
                            "Type": st.column_config.SelectboxColumn(
                                "Type d'absence",
                                options=["Blessé", "Malade", "Suspendu"],
                                required=True,
                            ),
                            "Durée": st.column_config.SelectboxColumn(
                                "Disponibilité",
                                options=["Incertain", "Out"],
                                required=True,
                            )
                        }
                    )
                    # Logique automatique : Si Suspendu -> Out
                    df_abs_dom.loc[df_abs_dom['Type'] == "Suspendu", "Durée"] = "Out"

                with col_ext:
                    st.subheader(f"🚀 {ext}")
                    # Configuration du tableau des absents Extérieur
                    df_abs_ext = st.data_editor(
                        pd.DataFrame(columns=['Joueur', 'Type', 'Durée']),
                        key=f"abs_ext_{idx}",
                        num_rows="dynamic",
                        use_container_width=True,
                        column_config={
                            "Type": st.column_config.SelectboxColumn(
                                "Type d'absence",
                                options=["Blessé", "Malade", "Suspendu"],
                                required=True,
                            ),
                            "Durée": st.column_config.SelectboxColumn(
                                "Disponibilité",
                                options=["Incertain", "Out"],
                                required=True,
                            )
                        }
                    )
                    # Logique automatique : Si Suspendu -> Out
                    df_abs_ext.loc[df_abs_ext['Type'] == "Suspendu", "Durée"] = "Out"

                # Bouton de validation pour passer à l'étape finale
                if st.checkbox("Valider l'impact des absences pour ce match", key=f"check_inf_{idx}"):
                    st.session_state.master_df.at[idx, 'GO_Etape3'] = True
                    st.session_state.master_df.at[idx, 'Absents_Dom'] = df_abs_dom.to_dict('records')
                    st.session_state.master_df.at[idx, 'Absents_Ext'] = df_abs_ext.to_dict('records')

        st.divider()
        if st.button("🤖 Envoyer l'Analyse d'Impact à l'IA"):
            valid_inf = st.session_state.master_df[st.session_state.master_df['GO_Etape3'] == True]
            prompt = "Analyse d'impact des effectifs demandée :\n\n"
            for _, r in valid_inf.iterrows():
                prompt += f"MATCH : {r['Match']}\n"
                prompt += f"Absents {dom} : {r['Absents_Dom']}\n"
                prompt += f"Absents {ext} : {r['Absents_Ext']}\n"
                prompt += "-------------------\n"
            st.code(prompt, language="text")

# --- ONGLET 4 : VERDICT ---
with tab4:
    st.header("4. Cotes & Revue de Presse")
    df_final = st.session_state.master_df[st.session_state.master_df['GO_Etape3'] == True]
    if not df_final.empty:
        edited_final = st.data_editor(df_final[['Match', 'Cote_Cible', 'Pari_Final']], use_container_width=True, hide_index=True)
        st.session_state.master_df.update(edited_final)
        
        if st.button("📰 Générer demande Revue de Presse"):
            st.code(f"Fais-moi la revue de presse pour : {df_final['Match'].tolist()}", language="text")
