import streamlit as st

# Configuration de la page
st.set_page_config(page_title="War Room - Betting Dashboard", page_icon="🎯", layout="wide")

# Titre principal
st.title("🎯 War Room : Interface de Commandement")
st.markdown("---")

# Création de deux colonnes
col1, col2 = st.columns(2)

with col1:
    st.subheader("🟢 Tirs Validés (Snipers)")
    st.success("FC Twente (DNB) - Cote : 2.02 - EV+ Massif")
    st.success("FC Porto (H -1.5) - Cote : 2.05 - Différentiel tactique")

with col2:
    st.subheader("❄️ Capital Roulant (Snowball)")
    st.info("Palier 1 : PSG (Victoire) - En attente...")
    st.info("Palier 2 : Feyenoord (Victoire 1.44) - Dimanche")

# Zone de test pour le futur calcul de Value Bet
st.markdown("---")
st.subheader("Calculateur Rapide de Value Bet")
cote_bookmaker = st.number_input("Entrez la cote du bookmaker (Scooore) :", min_value=1.01, value=2.00)
probabilite_ia = st.slider("Indice de Confiance IA (%) :", 0, 100, 55)

# Calcul basique de l'EV+
prob_implicite = (1 / cote_bookmaker) * 100
if probabilite_ia > prob_implicite:
    st.success(f"🔥 VALUE BET DÉTECTÉ ! Le bookmaker estime les chances à {prob_implicite:.1f}%. Notre IA dit {probabilite_ia}%.")
else:
    st.error("🔴 NO BET. Le risque est trop élevé par rapport à la cote.")
