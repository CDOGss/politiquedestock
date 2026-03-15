import streamlit as st
import pandas as pd
import numpy as np
import math

# ==========================================
# 1. PARAMÈTRES GLOBAUX
# ==========================================
COUT_PASSATION = 80.0
TAUX_POSSESSION = 0.15
NIVEAU_SERVICE_Z = 1.65
SEMAINES_PAR_MOIS = 4.33

st.set_page_config(page_title="Optimisation Stock - La Réunion", layout="wide")

st.title("🚢 Audit et Optimisation des Stocks (Outre-Mer)")
st.markdown("""
Cette application calcule vos points de commande et vos quantités économiques (EOQ). 
**Logique de calcul :** Intègre le rattrapage vers le *Niveau Cible de Confort* en cas de rupture pour protéger le BFR.
""")

st.divider()

# ==========================================
# 2. AFFICHAGE DU MODÈLE DE DONNÉES
# ==========================================
st.subheader("📋 Format du fichier attendu")
st.write("Votre fichier doit être au format **CSV (séparateur point-virgule)**.")

exemple_data = {
    'Code_SKU': ['REF-001', 'REF-002', 'REF-003'],
    'Description': ['Pompe à eau industrielle', 'Filtre à huile standard', 'Courroie de distribution'],
    'Famille': ['Plomberie', 'Automobile', 'Automobile'],
    'Criticite': [1, 3, 2],
    'Demande_Moy_Mensuelle': [45.0, 150.0, 30.0],
    'Ecart_Type_Demande': [12.5, 45.0, 8.0],
    'Lead_Time_Moyen_Semaines': [8, 6, 10],
    'Lead_Time_Max_Semaines': [12, 8, 14],
    'Prix_Achat_Unitaire': [150.00, 12.50, 45.00],
    'Coefficient_Approche_Total': [0.35, 0.28, 0.28],
    'MOQ': [5, 50, 10],
    'Multiple': [1, 50, 5],
    'Stock_Physique': [30, 80, 15],
    'Stock_Transit': [0, 100, 0]
}
df_exemple = pd.DataFrame(exemple_data)
st.dataframe(df_exemple, hide_index=True, use_container_width=True)

csv_template = df_exemple.iloc[0:0].to_csv(sep=';', index=False, decimal=',').encode('utf-8')
st.download_button(
    label="📥 Télécharger le modèle CSV vide",
    data=csv_template,
    file_name='template_stock_reunion.csv',
    mime='text/csv'
)

st.divider()

# ==========================================
# 3. INTERFACE DE TÉLÉVERSEMENT
# ==========================================
st.subheader("🚀 Lancer l'audit")
fichier_entree = st.file_uploader("Uploadez votre fichier rempli ici :", type=['csv'])

if fichier_entree is not None:
    try:
        df = pd.read_csv(fichier_entree, sep=';', decimal=',')
        st.success("Fichier chargé avec succès ! Calculs en cours...")
        
        # ==========================================
        # 4. MOTEUR DE CALCUL
        # ==========================================
        df['Prix_Revient'] = df['Prix_Achat_Unitaire'] * (1 + df['Coefficient_Approche_Total'])
        df['Cout_Possession_Annuel'] = df['Prix_Revient'] * TAUX_POSSESSION

        df['LT_Moyen_Mois'] = df['Lead_Time_Moyen_Semaines'] / SEMAINES_PAR_MOIS
        df['Sigma_LT_Mois'] = ((df['Lead_Time_Max_Semaines'] - df['Lead_Time_Moyen_Semaines']) / 3) / SEMAINES_PAR_MOIS

        variance_demande = df['Ecart_Type_Demande'] ** 2
        variance_delai = df['Sigma_LT_Mois'] ** 2
        df['Stock_Securite'] = NIVEAU_SERVICE_Z * np.sqrt(
            (df['LT_Moyen_Mois'] * variance_demande) + 
            ((df['Demande_Moy_Mensuelle'] ** 2) * variance_delai)
        )
        df['Stock_Securite'] = np.ceil(df['Stock_Securite'])

        df['Point_De_Commande'] = np.ceil((df['Demande_Moy_Mensuelle'] * df['LT_Moyen_Mois']) + df['Stock_Securite'])

        df['Demande_Annuelle'] = df['Demande_Moy_Mensuelle'] * 12
        df['EOQ_Theorique'] = np.sqrt((2 * df['Demande_Annuelle'] * COUT_PASSATION) / df['Cout_Possession_Annuel'])
        
        df['Couverture_Actuelle'] = df['Stock_Physique'] + df['Stock_Transit']

        # Nouvelle fonction d'ajustement intelligente corrigée (Niveau Cible)
        def ajuster_quantite(row):
            if row['Couverture_Actuelle'] <= row['Point_De_Commande']:
                # On calcule le niveau cible de confort (Alarme + Lot économique)
                niveau_cible = row['Point_De_Commande'] + row['EOQ_Theorique']
                # On commande ce qu'il faut pour atteindre ce niveau
                qte_base = niveau_cible - row['Couverture_Actuelle']
            else:
                # Si pas d'urgence, on recommande le lot standard théorique
                qte_base = row['EOQ_Theorique']
            
            # On vérifie qu'on respecte toujours le minimum fournisseur
            qte_base = max(qte_base, row['MOQ'])
            
            # Application stricte du multiple de conditionnement
            if row['Multiple'] > 0:
                qte_finale = math.ceil(qte_base / row['Multiple']) * row['Multiple']
            else:
                qte_finale = math.ceil(qte_base)
                
            return int(qte_finale)
            
        df['Quantite_A_Commander'] = df.apply(ajuster_quantite, axis=1)
        df['Action'] = np.where(df['Couverture_Actuelle'] <= df['Point_De_Commande'], "🚨 COMMANDER", "✅ OK")

        # ==========================================
        # 5. AFFICHAGE DES RÉSULTATS
        # ==========================================
        colonnes_export = [
            'Code_SKU', 'Description', 'Prix_Revient', 'Stock_Securite', 
            'Point_De_Commande', 'Couverture_Actuelle', 'Action', 'Quantite_A_Commander'
        ]
        df_export = df[colonnes_export]
        
        st.subheader("📊 Résultats de l'Audit")
        st.dataframe(df_export, hide_index=True, use_container_width=True)
        
        csv_export = df_export.to_csv(sep=';', index=False, decimal=',').encode('utf-8')
        st.download_button(
            label="📥 Télécharger le plan d'approvisionnement (CSV)",
            data=csv_export,
            file_name='plan_appro_reunion_optimise.csv',
            mime='text/csv'
        )

    except Exception as e:
        st.error(f"Erreur lors du traitement. Détail : {e}")
