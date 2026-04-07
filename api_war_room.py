import requests
import pandas as pd
import datetime
import os

# Sécurité : Récupération de la clé API cachée
API_TOKEN = os.environ.get("SPORTMONKS_TOKEN")

if not API_TOKEN:
    print("[!] ERREUR FATALE : Aucun Token API détecté.")
    exit()

def extraire_dynamique_api(team_id, team_name):
    print(f"[*] Infiltration de l'API Sportmonks pour : {team_name}...")
    
    # L'astuce : ".type" oblige Sportmonks à nous envoyer le nom de la stat en plus du code
    url = f"https://api.sportmonks.com/v3/football/teams/{team_id}?include=latest.statistics.type"
    headers = {"Authorization": API_TOKEN}

    try:
        reponse = requests.get(url, headers=headers)
        reponse.raise_for_status()
        donnees_brutes = reponse.json()
        
        if "data" not in donnees_brutes or "latest" not in donnees_brutes["data"]:
             print(f"[!] Pas de données récentes trouvées pour {team_name}.")
             return None

        derniers_matchs = donnees_brutes["data"]["latest"]
        
        # Initialisation de notre tableau de chasse
        stats = {"Poss": 0, "xG": 0, "SoT": 0, "Corners": 0}
        matchs_valides = 0

        # Boucle sur les 5 derniers combats
        for match in derniers_matchs[:5]:
            
            if "statistics" in match and isinstance(match["statistics"], list):
                match_a_des_stats = False
                
                # On fouille dans la liste pour trouver nos variables
                for stat in match["statistics"]:
                    
                    # 🛑 LE FILTRE VITAL : On ignore les stats de l'adversaire
                    if stat.get("participant_id") != team_id:
                        continue
                        
                    try:
                        val = float(stat.get("data", {}).get("value", 0))
                    except ValueError:
                        val = 0
                        
                    type_id = stat.get("type_id")
                    stat_info = stat.get("type", {})
                    stat_code = stat_info.get("code", "").lower()
                    
                    if type_id == 84 or "corner" in stat_code:
                        stats["Corners"] += val
                        match_a_des_stats = True
                    elif type_id == 86 or "target" in stat_code:
                        stats["SoT"] += val
                        match_a_des_stats = True
                    elif type_id == 45 or "possession" in stat_code:
                        stats["Poss"] += val
                        match_a_des_stats = True
                
                if match_a_des_stats:
                    matchs_valides += 1

        if matchs_valides == 0:
             print(f"[!] Aucune donnée statistique exploitable trouvée pour {team_name}.")
             return None

        # Construction de la ligne du CSV (Lissage des moyennes)
        synthese = {
            "Equipe": team_name,
            "Date_Extraction": datetime.datetime.now().strftime("%Y-%m-%d"),
            "Moy_Poss_5M": round(stats["Poss"] / matchs_valides, 1),
            "Moy_xG_5M": round(stats["xG"] / matchs_valides, 2),
            "Moy_SoT_5M": round(stats["SoT"] / matchs_valides, 1),
            "Moy_Corners_5M": round(stats["Corners"] / matchs_valides, 1)
        }
        
        print(f"[+] Succès : Dynamique des {matchs_valides} derniers matchs extraite pour {team_name}.")
        return synthese

    except Exception as e:
         print(f"[!] Erreur critique du système pour {team_name} : {e}")
         return None

# ==========================================
# ZONE DE LANCEMENT (SÉLECTION DES CIBLES)
# ==========================================
if __name__ == "__main__":
    # Liste des équipes à analyser. 
    # Ajoute les IDs Sportmonks de tes équipes ici.
    cibles = [
        {"nom": "FC_Barcelone", "id": 83}, 
        {"nom": "PSG", "id": 594}
    ]

    resultats = []
    
    for cible in cibles:
        data = extraire_dynamique_api(cible["id"], cible["nom"])
        if data:
            resultats.append(data)

    # Création du fichier final
    if resultats:
        df_final = pd.DataFrame(resultats)
        nom_fichier = "MASTER_DYNAMIQUE_API_5M.csv"
        df_final.to_csv(nom_fichier, index=False, sep=";")
        print(f"\n[OK] Fichier {nom_fichier} généré. Données froides prêtes pour la War Room.")
    else:
        print("\n[!] Échec total de l'extraction.")
