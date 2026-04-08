import requests
import pandas as pd
import datetime
from datetime import timedelta
import os

API_TOKEN = os.environ.get("SPORTMONKS_TOKEN")

if not API_TOKEN:
    print("[!] ERREUR FATALE : L'armurerie est verrouillée (Aucun Token API).")
    exit()

# ==========================================
# LE RADAR H-48 (Détection des cibles)
# ==========================================
def scanner_radar_h48():
    print("\n[*] =======================================")
    print("[*] ALLUMAGE DU RADAR H-48")
    print("[*] =======================================")
    
    date_debut = datetime.date.today().strftime("%Y-%m-%d")
    date_fin = (datetime.date.today() + timedelta(days=3)).strftime("%Y-%m-%d") # Scan sur 48-72h
    
    # ⚠️ À REMPLIR : Remplacer par les vrais IDs de tes ligues sur Sportmonks
    # On sait déjà que La Liga = 564. Trouve les autres (Premier League, Ligue 1, etc.)
    ligues_autorisees = [564, 8, 82, 1101, 401, 72, 462] 

    url_radar = f"https://api.sportmonks.com/v3/football/fixtures/between/{date_debut}/{date_fin}?include=participants"
    headers = {"Authorization": API_TOKEN}
    
    cibles_actives = []

    try:
        reponse = requests.get(url_radar, headers=headers)
        reponse.raise_for_status()
        matchs = reponse.json().get("data", [])
        
        for match in matchs:
            # On vérifie si le match appartient à l'un de nos championnats premium
            if match.get("league_id") in ligues_autorisees:
                participants = match.get("participants", [])
                for equipe in participants:
                    cibles_actives.append({
                        "nom": equipe.get("name", "Inconnu").replace(" ", "_"),
                        "id": equipe.get("id")
                    })
                    
        print(f"[+] Radar terminé : {len(cibles_actives)} équipes entrent sur le champ de bataille d'ici 48h.")
        return cibles_actives

    except Exception as e:
        print(f"[!] Panne du Radar H-48 : {e}")
        return []

# ==========================================
# EXTRACTION CLINIQUE (Dynamique + Infirmerie)
# ==========================================
def extraction_master(team_id, team_name):
    # Même code qu'avant, intact et chirurgical
    url = f"https://api.sportmonks.com/v3/football/teams/{team_id}?include=latest.statistics;upcoming"
    headers = {"Authorization": API_TOKEN}

    try:
        reponse = requests.get(url, headers=headers)
        reponse.raise_for_status()
        donnees = reponse.json()
        
        if "data" not in donnees:
             return None

        # 1. DYNAMIQUE
        derniers_matchs = donnees["data"].get("latest", [])
        stats = {"Poss": 0, "SoT": 0, "Corners": 0}
        matchs_valides = 0

        for match in derniers_matchs[:5]:
            match_a_des_stats = False
            if "statistics" in match and isinstance(match["statistics"], list):
                for stat in match["statistics"]:
                    if stat.get("participant_id") != team_id: continue
                    try:
                        val = float(stat.get("data", {}).get("value", 0))
                    except ValueError:
                        val = 0
                    
                    type_id = stat.get("type_id")
                    if type_id == 84:
                        stats["Corners"] += val
                        match_a_des_stats = True
                    elif type_id == 86:
                        stats["SoT"] += val
                        match_a_des_stats = True
                    elif type_id == 45:
                        stats["Poss"] += val
                        match_a_des_stats = True
                
            if match_a_des_stats: matchs_valides += 1

        # 2. INFIRMERIE
        absents_str = "Effectif Complet"
        upcoming_matchs = donnees["data"].get("upcoming", [])

        if upcoming_matchs:
            prochain_match_id = upcoming_matchs[0]["id"]
            url_med = f"https://api.sportmonks.com/v3/football/fixtures/{prochain_match_id}?include=sidelined.player;sidelined.type"
            
            reponse_med = requests.get(url_med, headers=headers)
            if reponse_med.status_code == 200:
                donnees_med = reponse_med.json()
                absents_liste = []
                sidelined_data = donnees_med.get("data", {}).get("sidelined", [])
                
                for blessure in sidelined_data:
                    if blessure.get("participant_id") == team_id:
                        sideline_detail = blessure.get("sideline", blessure)
                        nom = sideline_detail.get("player", {}).get("display_name", "Inconnu")
                        type_blessure = sideline_detail.get("type", {}).get("name", "Absence")
                        absents_liste.append(f"{nom} ({type_blessure})")
                
                if absents_liste:
                    absents_str = " | ".join(absents_liste)

        # 3. MATRICE
        if matchs_valides == 0: return None

        return {
            "Equipe": team_name,
            "Date_Extraction": datetime.datetime.now().strftime("%Y-%m-%d"),
            "Moy_Poss_5M": round(stats["Poss"] / matchs_valides, 1),
            "Moy_SoT_5M": round(stats["SoT"] / matchs_valides, 1),
            "Moy_Corners_5M": round(stats["Corners"] / matchs_valides, 1),
            "Infirmerie_H48": absents_str
        }

    except Exception:
         return None

# ==========================================
# LA SALLE DE COMMANDEMENT
# ==========================================
if __name__ == "__main__":
    
    # 1. On scanne l'horizon pour trouver qui joue dans les 48h
    cibles_dynamiques = scanner_radar_h48()

    if not cibles_dynamiques:
        print("[!] Aucun match détecté dans les ligues cibles pour les prochaines 48h. Fin des opérations.")
        exit()

    resultats = []
    
    # 2. On lance l'extraction uniquement sur les équipes détectées
    for cible in cibles_dynamiques:
        print(f"[*] Extraction des données pour : {cible['nom']}...")
        data = extraction_master(cible["id"], cible["nom"])
        if data:
            resultats.append(data)

    # 3. Génération du Master File
    if resultats:
        df_final = pd.DataFrame(resultats)
        nom_fichier = "WAR_ROOM_MATRICE_H48.csv"
        df_final.to_csv(nom_fichier, index=False, sep=";")
        print(f"\n[OK] Pipeline terminé. Fichier {nom_fichier} prêt avec les équipes du week-end.")
    else:
        print("\n[!] Échec de la mission. Aucun rapport généré.")
