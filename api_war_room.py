import requests
import pandas as pd
import datetime
import os

# 1. Sécurité : On récupère la clé secrète depuis l'environnement GitHub (ou ton PC)
API_TOKEN = os.environ.get("SPORTMONKS_TOKEN")

if not API_TOKEN:
    print("[!] ERREUR FATALE : Aucun Token API détecté. Fin de la mission.")
    exit()

def extraire_dynamique_api(team_id, team_name):
    print(f"[*] Interrogation de l'API Sportmonks pour : {team_name} (ID: {team_id})...")
    
    # Endpoint fictif optimisé pour Sportmonks v3 (récupère l'équipe, ses derniers matchs et stats)
    url = f"https://api.sportmonks.com/v3/football/teams/{team_id}?include=latest.statistics"
    headers = {"Authorization": API_TOKEN}

    try:
        reponse = requests.get(url, headers=headers)
        reponse.raise_for_status() # Vérifie que l'API n'est pas en panne
        
        donnees_brutes = reponse.json()
        
        # Sécurité de lecture : on vérifie que l'API renvoie bien les données attendues
        if "data" not in donnees_brutes or "latest" not in donnees_brutes["data"]:
             print(f"[!] Pas de données récentes trouvées pour {team_name}.")
             return None

        derniers_matchs = donnees_brutes["data"]["latest"]
        
        # On va stocker les totaux pour faire la moyenne
        stats = {"Poss": 0, "xG": 0, "Sh": 0, "SoT": 0, "Corners": 0}
        matchs_valides = 0

        # On boucle sur les 5 derniers matchs
        for match in derniers_matchs[:5]:
            if "statistics" in match:
                # La structure exacte dépendra du format JSON renvoyé par ton plan Sportmonks
                # Ici on simule l'extraction logique des données
                stats["xG"] += float(match["statistics"].get("expected_goals", 0))
                stats["SoT"] += int(match["statistics"].get("shots_on_target", 0))
                stats["Corners"] += int(match["statistics"].get("corners", 0))
                matchs_valides += 1

        if matchs_valides == 0:
             return None

        # 3. Création de la ligne de synthèse (Moyennes)
        synthese = {
            "Equipe": team_name,
            "Date_Extraction": datetime.datetime.now().strftime("%Y-%m-%d"),
            "Moy_xG_5M": round(stats["xG"] / matchs_valides, 2),
            "Moy_SoT_5M": round(stats["SoT"] / matchs_valides, 2),
            "Moy_Corners_5M": round(stats["Corners"] / matchs_valides, 2)
        }
        
        print(f"[+] Succès : Données cliniques extraites pour {team_name}.")
        return synthese

    except requests.exceptions.HTTPError as e:
        print(f"[!] Erreur HTTP lors de l'appel API pour {team_name} : {e}")
        return None
    except Exception as e:
         print(f"[!] Erreur inattendue pour {team_name} : {e}")
         return None

# ==========================================
# ZONE DE LANCEMENT DES ASSAUTS
# ==========================================
if __name__ == "__main__":
    # Liste des cibles : Tu dois remplacer par les VRAIS IDs Sportmonks
    # Ex: Le FC Barcelone a l'ID 83 sur Sportmonks.
    cibles = [
        {"nom": "FC_Barcelone", "id": 83}, 
        {"nom": "PSG", "id": 594}
    ]

    resultats = []
    
    for cible in cibles:
        data = extraire_dynamique_api(cible["id"], cible["nom"])
        if data:
            resultats.append(data)

    if resultats:
        df_final = pd.DataFrame(resultats)
        nom_fichier = "MASTER_DYNAMIQUE_API_5M.csv"
        df_final.to_csv(nom_fichier, index=False, sep=";")
        print(f"\n[OK] Fichier {nom_fichier} généré. La War Room est alimentée.")
    else:
        print("\n[!] Échec de l'extraction. Aucun fichier généré.")
