# Nouvelle fonction d'ajustement intelligente corrigée (Niveau Cible)
        def ajuster_quantite(row):
            if row['Couverture_Actuelle'] <= row['Point_De_Commande']:
                # On calcule le niveau cible de confort (Alarme + Lot économique)
                niveau_cible = row['Point_De_Commande'] + row['EOQ_Theorique']
                # On commande ce qu'il faut pour atteindre ce niveau
                qte_base = niveau_cible - row['Couverture_Actuelle']
            else:
                # Si pas d'urgence, on recommande le lot standard
                qte_base = row['EOQ_Theorique']
            
            # On vérifie qu'on respecte toujours le minimum fournisseur
            qte_base = max(qte_base, row['MOQ'])
            
            # Application stricte du multiple de conditionnement
            if row['Multiple'] > 0:
                qte_finale = math.ceil(qte_base / row['Multiple']) * row['Multiple']
            else:
                qte_finale = math.ceil(qte_base)
                
            return int(qte_finale)
