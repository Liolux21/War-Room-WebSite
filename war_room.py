import streamlit as st
import pandas as pd

# 1. Chargement de la base de données des joueurs
@st.cache_data
def load_players_db():
    try:
        # Lecture du fichier CSV que tu m'as fourni
        df = pd.read_csv("MASTER_ANALYSE_2026-04-02.csv")
        # On crée un dictionnaire : { 'Nom Equipe': [Liste des Joueurs] }
        players_db = df.groupby('Equipe')['Joueur'].apply(list).to_dict()
        return players_db
    except:
        # Si le fichier n'est pas trouvé, on retourne un dictionnaire vide pour éviter le crash
        return {}

players_db = load_players_db()

# ... (Garder le début du code précédent pour le session_state) ...

# --- ONGLET 3 : L'INFIRMERIE (VERSION LISTE DÉROULANTE) ---
with tab3:
    st.header("3. État des troupes (Sélection par effectif)")
    
    df_inf = st.session_state.master_df[st.session_state.master_df['GO_Etape2'] == True]
    
    if df_inf.empty:
        st.info("Veuillez valider des matchs à l'étape 2 pour accéder aux effectifs.")
    else:
        for idx, row in df_inf.iterrows():
            with st.expander(f"🏥 Infirmerie : {row['Match']}", expanded=True):
                dom, ext = row['Match'].split(' vs ')
                
                # Récupération des listes de joueurs pour les deux équipes
                list_players_dom = sorted(players_db.get(dom, []))
                list_players_ext = sorted(players_db.get(ext, []))

                col_dom, col_ext = st.columns(2)
                
                with col_dom:
                    st.subheader(f"🏠 {dom}")
                    df_abs_dom = st.data_editor(
                        pd.DataFrame(columns=['Joueur', 'Type', 'Durée']),
                        key=f"abs_dom_{idx}",
                        num_rows="dynamic",
                        use_container_width=True,
                        column_config={
                            "Joueur": st.column_config.SelectboxColumn(
                                "Nom du Joueur",
                                options=list_players_dom, # Liste limitée aux joueurs de l'équipe domicile
                                required=True,
                            ),
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
                    df_abs_dom.loc[df_abs_dom['Type'] == "Suspendu", "Durée"] = "Out"

                with col_ext:
                    st.subheader(f"🚀 {ext}")
                    df_abs_ext = st.data_editor(
                        pd.DataFrame(columns=['Joueur', 'Type', 'Durée']),
                        key=f"abs_ext_{idx}",
                        num_rows="dynamic",
                        use_container_width=True,
                        column_config={
                            "Joueur": st.column_config.SelectboxColumn(
                                "Nom du Joueur",
                                options=list_players_ext, # Liste limitée aux joueurs de l'équipe extérieur
                                required=True,
                            ),
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
                    df_abs_ext.loc[df_abs_ext['Type'] == "Suspendu", "Durée"] = "Out"

                if st.checkbox("Valider l'impact des absences", key=f"check_inf_{idx}"):
                    st.session_state.master_df.at[idx, 'GO_Etape3'] = True
                    st.session_state.master_df.at[idx, 'Absents_Dom'] = df_abs_dom.to_dict('records')
                    st.session_state.master_df.at[idx, 'Absents_Ext'] = df_abs_ext.to_dict('records')

        # ... (Garder le bouton de génération de prompt IA) ...
