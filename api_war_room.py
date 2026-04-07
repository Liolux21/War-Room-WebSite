import requests
import pandas as pd
import datetime
import os

API_TOKEN = os.environ.get("SPORTMONKS_TOKEN")

if not API_TOKEN:
    print("[!] ERREUR FATALE : Aucun Token API détecté.")
    exit()

def extraire_donnees_api(team_id, team_name):
    print(f"\n[*] =======================================")
    print(f"[*] INFILTRATION DU SERVEUR POUR : {team_name}")
    print(f"[*] =======================================")
    
    # CORRECTION VITALE : Utilisation du point-virgule (;) pour séparer les modules dans l'API V3
    url_team = f"https://api.sportmonks.com/v3/football/teams/{team_id}?include=latest.statistics;latest.xgfixture;upcoming"
    headers = {"Authorization": API_TOKEN}

    try:
        reponse_team = requests.get(url_team, headers=headers)
        reponse_team.raise_for_status()
        donnees_team = reponse_team.json()
        
        if "data" not in donnees_team:
             print(f"[!] Pas de données trouvées pour {team_name}.")
             return None

        # ==========================================
        # 1. ANALYSE DE LA DYNAMIQUE (5 Derniers)
        # ==========================================
        derniers_matchs = donnees_team["data"].get("latest", [])
        stats = {"Poss": 0, "xG": 0, "SoT": 0, "Corners": 0}
        matchs_valides = 0

        for match in derniers_matchs[:5]:
            match_a_des_stats = False
            
            # Stats Classiques (Corners 84, Tirs Cadrés 86, Possession 45)
            if "statistics" in match and isinstance(match["statistics"], list):
                for stat in match["statistics"]:
                    if stat.get("participant_id") != team_id:
                        continue
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

            # Stats xG (Code 5304)
            if "xgfixture" in match and isinstance(match["xgfixture"], list):
                for xg_stat in match["xgfixture"]:
                    if xg_stat.get("participant_id") != team_id:
                        continue
                    
                    if xg_stat.get("type_id") == 5304:
                        try:
                            val = float(xg_stat.get("data", {}).get("value", 0))
                            stats["xG"] += val
                            match_a_des_stats = True
                        except ValueError:
                            pass
                
            if match_a_des_stats:
                matchs_valides += 1

        if matchs_valides == 0:
             print(f"[!] Aucune donnée statistique exploitable trouvée pour {team_name}.")
             return None

        # ==========================================
        # 2. ANALYSE DE L'INFIRMERIE (Prochain Match)
        # ==========================================
        absents_str = "Aucun absent majeur déclaré"
        upcoming_matchs = donnees_team["data"].get("upcoming", [])

        if upcoming_matchs:
            prochain_match_id = upcoming_matchs[0]["id"]
            
            # CORRECTION : Point-virgule pour l'endpoint Fixture
            url_fixture = f"https://api.sportmonks.com/v3/football/fixtures/{prochain_match_id}?include=sidelined.player;sidelined.type"
            
            reponse_fixture = requests.get(url_fixture, headers=headers)
            if reponse_fixture.status_code == 200:
                donnees_fixture = reponse_fixture.json()
                absents_liste = []
                sidelined_data = donnees_fixture.get("data", {}).get("sidelined", [])
                
                for blessure in sidelined_data:
                    if blessure.get("participant_id") == team_id:
                        sideline_detail = blessure.get("sideline", blessure)
                        nom_joueur = sideline_detail.get("player", {}).get("display_name", "Inconnu")
                        type_blessure = sideline_detail.get("type", {}).get("name", "Absence")
                        absents_liste.append(f"{nom_joueur} ({type_blessure})")
                
                if absents_liste:
                    absents_str = " | ".join(absents_liste)
        
        print(f"[+] Bilan Médical : {absents_str}")

        # ==========================================
        # 3. SYNTHÈSE TOTALE POUR LE CSV
        # ==========================================
        synthese = {
            "Equipe": team_name,
            "Date_Extraction": datetime.datetime.now().strftime("%Y-%m-%d"),
            "Moy_Poss_5M": round(stats["Poss"] / matchs_valides, 1),
            "Moy_xG_5M": round(stats["xG"] / matchs_valides, 2),
            "Moy_SoT_5M": round(stats["SoT"] / matchs_valides, 1),
            "Moy_Corners_5M": round(stats["Corners"] / matchs_valides, 1),
            "Infirmerie": absents_str
        }
        
        print(f"[+] Succès : Dynamique lissée calculée sur {matchs_valides} matchs.")
        return synthese

    except requests.exceptions.HTTPError as err:
        print(f"[!] Erreur API ({err.response.status_code}) pour {team_name} : {err.response.text}")
        return None
    except Exception as e:
         print(f"[!] Erreur critique du système pour {team_name} : {e}")
         return None

# ==========================================
# CIBLAGE ET EXÉCUTION
# ==========================================
if __name__ == "__main__":
    cibles = [
        {"nom": "FC_Barcelone", "id": 83}, 
        {"nom": "PSG", "id": 594}
    ]

    resultats = []
    for cible in cibles:
        data = extraire_donnees_api(cible["id"], cible["nom"])
        if data:
            resultats.append(data)

    if resultats:
        df_final = pd.DataFrame(resultats)
        nom_fichier = "MASTER_DYNAMIQUE_API_5M.csv"
        df_final.to_csv(nom_fichier, index=False, sep=";")
        print(f"\n[OK] Fichier {nom_fichier} généré. Transmission vers la War Room autorisée.")
    else:
        print("\n[!] Échec total de l'extraction.")
