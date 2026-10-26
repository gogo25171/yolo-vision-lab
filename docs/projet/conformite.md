# Conformité (RGPD, licences)

!!! warning "Ceci n'est pas un avis juridique"
    Cette page recense les points d'attention. Pour un déploiement réel, faites valider votre cas par un
    juriste ou votre DPO.

## Données personnelles (RGPD)

Les images de personnes identifiables et les **plaques d'immatriculation** sont des données personnelles.
Leur traitement par une caméra « augmentée » est encadré, en France, par la CNIL :

- **Base légale et finalité** définies avant le déploiement (comptage, sécurité…) ; filmer la voie publique
  est en principe réservé aux autorités publiques habilitées.
- **Information** des personnes filmées (panneau, mentions).
- **Minimisation** : ne garder que ce qui est nécessaire. Par exemple, désactiver les plaques
  (`PLATES_ENABLED=false`) pour du simple comptage, ou ne conserver que `summary.json`.
- **Durée de conservation** limitée des vidéos annotées et des CSV contenant des plaques.
- **Analyse d'impact (AIPD)** souvent requise pour la vidéo augmentée.

Ressources : [CNIL — caméras augmentées dans les espaces publics](https://www.cnil.fr/fr/deploiement-de-cameras-augmentees-dans-les-espaces-publics).

## Règlement européen sur l'IA (AI Act)

- La **catégorisation biométrique** qui déduit des caractéristiques sensibles (origine, opinions, religion,
  orientation sexuelle…) est **interdite**.
- La catégorisation biométrique selon des attributs sensibles ou protégés (par exemple le sexe ou l'âge),
  ainsi que l'identification biométrique à distance, relèvent des systèmes **à haut risque**.

C'est pourquoi Traffic Vision n'intègre ni reconnaissance faciale, ni estimation du genre ou de la
corpulence (voir [Classes détectées](../fonctionnalites/classes.md#attributs-des-personnes)).

## Licences logicielles

| Composant | Licence | Conséquence |
|---|---|---|
| Ultralytics YOLO | **AGPL-3.0** | Tout logiciel qui l'intègre et est distribué **ou exposé sur un réseau** doit publier son code source sous AGPL-3.0, sauf licence entreprise Ultralytics |
| Poids YOLO26 / YOLOE | AGPL-3.0 (Ultralytics) | Idem |
| fast-alpr, fast-plate-ocr, open-image-models | MIT | Libre, mention de la licence |
| OpenCV | Apache-2.0 | Libre |
| Traffic Vision | **AGPL-3.0-or-later** | Choisie pour être compatible avec Ultralytics |

## Licences des données de test

Voir [Données de test](donnees-test.md) et `samples/SOURCES.md`.
