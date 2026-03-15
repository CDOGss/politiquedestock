import pandas as pd
import numpy as np
import math
import tkinter as tk
from tkinter import filedialog
import os

# ==========================================
# 1. PARAMÈTRES GLOBAUX (Contextualisés Réunion)
# ==========================================
COUT_PASSATION = 80.0      # Coût administratif par commande en euros
TAUX_POSSESSION = 0.15     # 15% du prix de revient
NIVEAU_SERVICE_Z = 1.65    # Taux de service visé : 95%
SEMAINES_PAR_MOIS = 4.33

def optimiser_stock_local():
    # Initialisation de la fenêtre de dialogue (on la cache pour ne garder que le pop-up)
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True) # Garde la fenêtre au premier plan

    # ==========================================
    # 2. SÉLECTION DU FICHIER (Fenêtre Windows)
    # ==========================================
    print("Ouverture de la fenêtre de sélection. Veuillez choisir votre fichier CSV...")
    fichier_entree = filedialog.askopenfilename(
        title="Sélectionnez votre export de stock CSV",
        filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")]
    )
    
    if not fichier_entree:
        print("Aucun fichier sélectionné. Fin de l'audit.")
        return
        
    print(f"\nLecture en cours : {os.path.basename(fichier_entree)}")

    try:
        # Lecture du fichier (adaptation aux formats français avec point-virgule)
        df = pd.read_csv(fichier_entree, sep=';', decimal=',')
    except Exception as e:
        print(f"Erreur lors de la lecture. Vérifiez que c'est un CSV avec points-virgules : {e}")
        return

    # ==========================================
    # 3. CALCULS FINANCIERS (Impact Octroi de Mer)
    # ==========================================
    df['Prix_Revient'] = df['Prix_Achat_Unitaire'] * (1 + df['Coefficient_Approche_Total'])
    df['Cout_Possession_Annuel'] = df['Prix_Revient'] * TAUX_POSSESSION

    # ==========================================
    # 4. HARMONISATION TEMPORELLE & VARIANCE LT
    # ==========================================
    df['LT_Moyen_Mois'] = df['Lead_Time_Moyen_Semaines'] / SEMAINES_PAR_MOIS
    df['Sigma_LT_Mois'] = ((df['Lead_Time_Max_Semaines'] - df['Lead_Time_Moyen_Semaines']) / 3) / SEMAINES_PAR_MOIS

    # ==========================================
    # 5. CALCUL DU STOCK DE SÉCURITÉ
    # ==========================================
    variance_demande = df['Ecart_Type_Demande'] ** 2
    variance_delai = df['Sigma_LT_Mois'] ** 2
    
    df['Stock_Securite'] = NIVEAU_SERVICE_Z * np.sqrt(
        (df['LT_Moyen_Mois'] * variance_demande) + 
        ((df['Demande_Moy_Mensuelle'] ** 2) * variance_delai)
    )
    df['Stock_Securite'] = np.ceil(df['Stock_Securite'])

    # ==========================================
    # 6. POINT DE COMMANDE
    # ==========================================
    df['Point_De_Commande'] = np.ceil((df['Demande_Moy_Mensuelle'] * df['LT_Moyen_Mois']) + df['Stock_Securite'])

    # ==========================================
    # 7. QUANTITÉ ÉCONOMIQUE (Wilson adapté)
    # ==========================================
    df['Demande_Annuelle'] = df['Demande_Moy_Mensuelle'] * 12
    df['EOQ_Theorique'] = np.sqrt((2 * df['Demande_Annuelle'] * COUT_PASSATION) / df['Cout_Possession_Annuel'])
    
    def ajuster_quantite(row):
        qte = max(row['EOQ_Theorique'], row['MOQ'])
        if row['Multiple'] > 0:
            qte = math.ceil(qte / row['Multiple']) * row['Multiple']
        return int(qte)
        
    df['Quantite_A_Commander'] = df.apply(ajuster_quantite, axis=1)

    # ==========================================
    # 8. STATUT D'ACTION IMMÉDIATE
    # ==========================================
    df['Couverture_Actuelle'] = df['Stock_Physique'] + df['Stock_Transit']
    df['Action'] = np.where(df['Couverture_Actuelle'] <= df['Point_De_Commande'], "COMMANDER", "OK")

    # ==========================================
    # 9. SAUVEGARDE DU RÉSULTAT
    # ==========================================
    colonnes_export = [
        'Code_SKU', 'Description', 'Prix_Revient', 'Stock_Securite', 
        'Point_De_Commande', 'Couverture_Actuelle', 'Action', 'Quantite_A_Commander'
    ]
    df_export = df[colonnes_export]
    
    print("\nCalculs terminés ! Veuillez choisir où sauvegarder le résultat...")
    fichier_sortie = filedialog.asksaveasfilename(
        title="Enregistrer le plan d'approvisionnement sous...",
        defaultextension=".csv",
        initialfile="plan_appro_reunion.csv",
        filetypes=[("Fichiers CSV", "*.csv")]
    )
    
    if fichier_sortie:
        df_export.to_csv(fichier_sortie, sep=';', index=False, decimal=',')
        print(f"\nAudit terminé avec succès ! Fichier sauvegardé ici : {fichier_sortie}")
    else:
        print("\nSauvegarde annulée.")

# Lancement du programme
if __name__ == "__main__":
    optimiser_stock_local()