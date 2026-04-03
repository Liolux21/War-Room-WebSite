import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="War Room - Betting Pipeline", layout="wide", initial_sidebar_state="collapsed")
st.title("🎯 War Room - Entonnoir d'Investissement")

# 1. Initialisation de la base de données (Session State)
# Si c'est la première fois qu'on charge la page, on crée un tableau vide avec toutes les colonnes nécessaires
if 'master_df' not in st.session_state:
    st.session_state.master_df = pd.DataFrame(columns=[
        'Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1',
        '1x2', 'Handicap_Asian', 'BTTS', 'RTP', 'RTA', 'Attaques_Dangeureuses', 'Tirs_Cadrés', 'GO_Etape2',
        'Absents_Dom', 'Absents_Ext', 'GO_Etape3',
        'Cote_Cible', 'Prob_Implicite', 'Value_EV_Plus', 'Pari_Final'
    ])
    
    # Ligne d'exemple pour montrer le fonctionnement (tu pourras la supprimer)
    st.session_state.master_df.loc[0] = ['2026-04-06', '12:30', 'Udinese vs Como', 'Serie A', 'Como', '75%', False, 
                                         '', '', '', '', '', '', '', False, 
                                         '', '', False, 
                                         '', '', '', '']

# Fonction pour mettre à jour le master_df après une édition
def update_df(edited_df):
    st.session_state.master_df.update(edited_df)

# Création des 4 onglets de l'entonnoir
tab1, tab2, tab3, tab4 = st.tabs(["📡 1. Le Radar (Import)", "📊 2. Salle des Machines (AIStats)", "🏥 3. Infirmerie", "🧮 4. Calculette & Revue de presse"])

# ==========================================
# ONGLET 1 : LE RADAR
# ==========================================
with tab1:
    st.header("Étape 1 : Filtrage du Calendrier")
    st.info("Ici, le CSV du calendrier remontera. Coche GO_Etape1 pour garder les matchs intéressants.")
    
    # Colonnes visibles pour cette étape
    cols_etape1 = ['Date', 'Heure', 'Match', 'Ligue', 'Favori', 'Confiance_Initiale', 'GO_Etape1']
    
    edited_etape1 = st.data_editor(
        st.session_state.master_df[cols_etape1],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )
    update_df(edited_etape1)
    
    st.divider()
    if st.button("🤖 Générer le rapport IA pour filtrer l'Étape 1"):
        # On ne prend que les matchs actuels
        prompt = "Voici les matchs du calendrier avec l'indice de confiance initial. Lesquels dois-je passer à l'étape 2 (GO) et lesquels dois-je éliminer ?\n\n"
        prompt += edited_etape1.to_string(index=False)
        st.code(prompt, language="text")

# ==========================================
# ONGLET 2 : SALLE DES MACHINES (AISTATS)
# ==========================================
with tab2:
    st.header("Étape 2 : Saisie des données statistiques")
    st.info("Saisis les statistiques manuelles pour les matchs validés à l'étape 1. Coche GO_Etape2 si la stat tient la route.")
    
    # Filtrer uniquement les matchs avec GO_Etape1 == True
    df_etape2 = st.session_state.master_df[st.session_state.master_df['GO_Etape1'] == True]
    
    if df_etape2.empty:
        st.warning("Aucun match validé à l'étape 1.")
    else:
        cols_etape2 = ['Match', '1x2', 'Handicap_Asian', 'BTTS', 'RTP', 'RTA', 'Attaques_Dangeureuses', 'Tirs_Cadrés', 'GO_Etape2']
        
        edited_etape2 = st.data_editor(
            df_etape2[cols_etape2],
            use_container_width=True,
            hide_index=True
        )
        update_df(edited_etape2)
        
        st.divider()
        if st.button("🤖 Générer le rapport IA pour filtrer l'Étape 2"):
            prompt = "Voici les statistiques AIStats des matchs présélectionnés. Peux-tu croiser ces chiffres avec tes matrices de données et me dire quels matchs je dois cocher en 'GO' pour l'étape de l'infirmerie ?\n\n"
            prompt += edited_etape2.to_string(index=False)
            st.code(prompt, language="text")

# ==========================================
# ONGLET 3 : L'INFIRMERIE
# ==========================================
with tab3:
    st.header("Étape 3 : Absences et Suspensions")
    st.info("Renseigne les joueurs clés absents. Coche GO_Etape3 si l'effectif valide l'avantage.")
    
    df_etape3 = st.session_state.master_df[st.session_state.master_df['GO_Etape2'] == True]
    
    if df_etape3.empty:
        st.warning("Aucun match validé à l'étape 2.")
    else:
        cols_etape3 = ['Match', 'Absents_Dom', 'Absents_Ext', 'GO_Etape3']
        
        edited_etape3 = st.data_editor(
            df_etape3[cols_etape3],
            use_container_width=True,
            hide_index=True
        )
        update_df(edited_etape3)
        
        st.divider()
        if st.button("🤖 Générer le rapport IA pour filtrer l'Étape 3"):
            prompt = "Voici les absences médicales et suspensions pour les matchs de la shortlist. L'asymétrie d'information est-elle confirmée ? Lesquels passent en étape finale ?\n\n"
            prompt += edited_etape3.to_string(index=False)
            st.code(prompt, language="text")

# ==========================================
# ONGLET 4 : CALCULETTE EV+ ET REVUE DE PRESSE
# ==========================================
with tab4:
    st.header("Étape 4 : Validation EV+ et Revue de Presse Finale")
    st.info("Entre les cotes pour les derniers survivants.")
    
    df_etape4 = st.session_state.master_df[st.session_state.master_df['GO_Etape3'] == True]
    
    if df_etape4.empty:
        st.warning("Aucun match n'a survécu jusqu'ici.")
    else:
        cols_etape4 = ['Match', 'Pari_Final', 'Cote_Cible', 'Prob_Implicite', 'Value_EV_Plus']
        
        edited_etape4 = st.data_editor(
            df_etape4[cols_etape4],
            use_container_width=True,
            hide_index=True
        )
        update_df(edited_etape4)
        
        st.divider()
        st.subheader("La Requête Ultime")
        if st.button("🤖 Générer la demande de Revue de Presse"):
            # On prend la première ligne pour l'exemple
            match_cible = edited_etape4.iloc[0]['Match'] if not edited_etape4.empty else "[Équipe A] vs [Équipe B]"
            
            prompt = f"Peux-tu me faire une analyse approfondie du match {match_cible} en croisant nos données CSV avec les dernières infos de la presse locale et dans les conférences de presse d'avant-match ?\n\n"
            prompt += "Focus particulier sur :\n"
            prompt += "1. Le Onze Probable : Y a-t-il des absents de dernière minute ou des retours de sélections compliqués ?\n"
            prompt += "2. L'Intention Tactique : Le coach a-t-il évoqué une rotation ou une urgence de points ?\n"
            prompt += "3. Le Climat Club : Tensions internes, ferveur, enjeux ?\n"
            prompt += "4. Verdict Humain vs IA : Est-ce que ces infos confirment ou infirment la Value détectée ?\n\n"
            prompt += "Voici nos données pour ce match :\n"
            prompt += st.session_state.master_df[st.session_state.master_df['Match'] == match_cible].to_string(index=False)
            
            st.code(prompt, language="text")
