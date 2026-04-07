import pandas as pd
import requests
import time
import datetime

def extraire_dynamique_fbref(url_equipe, nom_equipe):
    print(f"[*] Infiltration des serveurs FBref pour : {nom_equipe}...")
    
    # Un User-Agent robuste pour ne pas passer pour un bot bas de gamme
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # 1. Requête HTTP vers la page
        reponse = requests.get(url_equipe, headers=headers)
        reponse.raise_for_status() # Vérifie si on s'est fait bloquer
        
        # 2. Pandas lit tous les tableaux HTML de la page
        # match="Match Logs" permet de cibler le bon tableau
        tableaux = pd.read_html(reponse.text, match="Match Logs")
        df = tableaux[0]

        # 3. Nettoyage du tableau (FBref utilise souvent des multi-index complexes)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(0)

        # 4. Filtrage : On ne garde que les matchs terminés (où il y a un résultat)
        df_joues = df[df['Result'].notna()].copy()
        
        # 5. On isole les 5 DERNIERS matchs (La Dynamique)
        df_5_derniers = df_joues.tail(5)

        # 6. Extraction et conversion des colonnes clés en nombres
        colonnes_a_moyenner = ['Poss', 'xG', 'xGA', 'Sh', 'SoT']
        
        # On vérifie que les colonnes existent bien dans ce tableau spécifique
        stats_calculees = {}
        for col in colonnes_a_moyenner:
            if col in df_5_derniers.columns:
                df_5_derniers.loc[:, col] = pd.to_numeric(df_5_derniers[col], errors='coerce')
                stats_calculees[f"Moy_{col}_5M"] = round(df_5_derniers[col].mean(), 2)

        # 7. Création de la ligne de synthèse
        synthese = {
            "Equipe": nom_equipe,
            "Date_Extraction": datetime.datetime.now().strftime("%Y-%m-%d"),
            **stats_calculees
        }

        # Pause obligatoire pour ne pas se faire bannir par FBref
        time.sleep(4) 
        
        print(f"[+] Données extraites avec succès pour {nom_equipe}.")
        return synthese

    except Exception as e:
        print(f"[!] ERREUR lors de l'extraction pour {nom_equipe} : {e}")
        return None

# ==========================================
# ZONE DE LANCEMENT DES ASSAUTS
# ==========================================
if __name__ == "__main__":
    # Liste des cibles avec les VÉRITABLES URLs FBref (onglet "Scores & Fixtures")
    cibles = [
        {"nom": "FC_Barcelone", "url": "https://fbref.com/en/squads/206d90db/matchlogs/all_comps/schedule/Barcelona-Scores-and-Fixtures"},
        {"nom": "PSG", "url": "https://fbref.com/en/squads/70d6c58e/matchlogs/all_comps/schedule/Paris-Saint-Germain-Scores-and-Fixtures"}
    ]

    resultats = []
    
    for cible in cibles:
        data = extraire_dynamique_fbref(cible["url"], cible["nom"])
        if data:
            resultats.append(data)

    # Exportation du fichier maître pour la War Room
    if resultats:
        df_final = pd.DataFrame(resultats)
        nom_fichier = "MASTER_DYNAMIQUE_5M.csv"
        df_final.to_csv(nom_fichier, index=False, sep=";")
        print(f"\n[OK] Fichier {nom_fichier} généré et prêt pour l'analyse Big Picture.")
    else:
        print("\n[!] Échec total de la mission. Aucun fichier généré.")
