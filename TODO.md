# TODO

Feuille de route de **YOLO Vision Lab**. Les priorités sont dans l'ordre ; cocher au fur et à mesure.

> **Vision** : un laboratoire qui permet à des personnes **non expérimentées** de comprendre, tester et
> brancher sur leurs outils des projets de vision (ceux de l'équipe Ultralytics/YOLO, de Roboflow, les
> nôtres, ceux de la communauté), **mis à jour sur les dernières versions**, sur **n'importe quelle
> plateforme** (PC Windows, serveur Linux sans GPU, machine multi-GPU, Mac, Jetson…).

## 🚧 Reprise — état au 26/10/2026 (branche `refonte/vision-lab`)

- [x] Restructuration : socle commun `vision_lab/` + un dossier par projet dans `projets/`
- [x] Projet `distance_vitesse` (ex-`traffic_vision`) : fonctionne, testé sur les 5 vidéos
- [x] Projet `solutions` (15 solutions Ultralytics) : testé `count` et `heatmap`
- [x] Intégrations communes testées : API REST/WebSocket/MJPEG, webhooks, diffusion RTMP (fichier .flv)
- [x] `python -m vision_lab doctor` : vérification de l'installation
- [x] Python 3.14 validé (torch 2.11 cu128, ultralytics 8.4, supervision 0.31, transformers 5)
- [ ] **Football** : code roboflow/sports copié et branché (`projets/football`), modèles et vidéos téléchargés
      (`python -m vision_lab football setup --videos`) mais **pas encore exécuté** (exécution des modèles
      `.pt` téléchargés bloquée dans la session de l'assistant) → tester `--mode players|ball|pitch`
- [ ] Football : `sv.ByteTrack` n'existe plus dans supervision 0.31 → modes `tracking`, `teams`, `radar`
      cassés. Remplacer par le suivi Ultralytics (`model.track`) ou le paquet `trackers` de Roboflow
- [ ] Documentation : mettre à jour les pages pour la nouvelle structure (commandes `python -m vision_lab …`,
      pages Prérequis, Intégrations, Projets) puis `mkdocs build --strict`
- [ ] Docker : rebuild non testé (moteur Docker Desktop en erreur 500 pendant la session → redémarrer
      Docker Desktop puis `docker compose build`)
- [ ] MQTT : non testé faute de broker (`docker run -p 1883:1883 eclipse-mosquitto`)
- [x] Dépôt GitHub renommé en `yolo-vision-lab`, description et sujets mis à jour, dossier local renommé
- [ ] Activer GitHub Pages (Settings > Pages > GitHub Actions) et fusionner la branche dans `main`
- [ ] `.dockerignore` a été remplacé par le modèle de `docker init` : y remettre `models/`, `samples/`,
      `output/`, `site/`, `docs/` (contexte de build énorme sinon)

## 0. Organisation du dépôt (à faire en premier à la reprise)

- [x] Dépendances : socle en racine (`requirements.txt`), propres à chaque projet dans
      `projets/<projet>/requirements.txt`
- [ ] **Passer à [uv](https://docs.astral.sh/uv/)** : `pyproject.toml` avec un *workspace* (racine = socle,
      un membre par projet), `uv.lock` commité, `uv sync --extra <projet>`, index PyTorch CPU/CUDA choisi
      selon le matériel (`[tool.uv.sources]`), `uv run vision-lab …` ; adapter Dockerfile et CI (`astral-sh/setup-uv`)
- [ ] Paramètres par projet : un `projets/<projet>/.env.example` et un `README.md` (ce que fait le projet,
      prérequis, paramètres, exemples) ; la racine ne garde que les paramètres communs (affichage, API,
      webhooks, MQTT, diffusion, MODELS_DIR, OUTPUT_DIR) ; `settings.py` de chaque projet lit sa section
- [ ] Docs : page « Prérequis » (socle + par projet) générée depuis ces fichiers

## 1. Interface du laboratoire (PRIORITÉ)

Point d'entrée central pour tout le monde : `python -m vision_lab ui` (ou Docker) ouvre une page web.

- [ ] Démarrer avec **le minimum** : l'interface doit se lancer même sans GPU, sans PyTorch, sans modèles
      (FastAPI + page statique ; les projets sont chargés à la demande)
- [ ] **Catalogue des projets** : fiche par projet (ce que ça fait, démo vidéo, prérequis, état
      « prêt / il manque X »), bouton « Essayer » sur une vidéo d'exemple, une webcam ou un fichier envoyé
- [ ] **Vérification de l'environnement** dans l'interface (version graphique de `doctor`) : Python,
      pilote NVIDIA, CUDA, nombre de GPU, RAM, ffmpeg, paquets manquants par projet
      - [ ] Message guidé quand il manque quelque chose (pilote, matériel, paquet) avec la commande ou le lien
      - [ ] Si tout est présent : ne rien dire et lancer
- [ ] **Profils matériels automatiques** : détecter CPU seul / 1 GPU / plusieurs GPU (NVIDIA, Apple MPS,
      Intel OpenVINO, AMD ROCm) et choisir modèle, taille d'entrée, export (TensorRT/OpenVINO) ; afficher
      « configuration limitée : réglé en mode X, conseillé : Y pour aller au maximum »
- [ ] Multi-GPU : répartir les caméras/projets sur les GPU (`DEVICE=0`, `DEVICE=1`…)
- [ ] Installation assistée d'un projet (bouton « installer les dépendances » → `pip install -r projets/<p>/requirements.txt`)
- [ ] Configuration sans éditer le `.env` : formulaires (source, mode, zones, intégrations), sauvegarde
- [ ] Éditeur de zones et d'objets statiques dans le navigateur ; assistant de calibration (4 points au sol)
- [ ] Tableau de bord temps réel : flux, compteurs, événements, dernières plaques ; multi-caméras
- [ ] Assistant « brancher à mes outils » : générer l'URL webhook, le topic MQTT, la config Home Assistant /
      Node-RED / n8n, la clé YouTube, avec un bouton « tester »
- [ ] Comparaison côte à côte de deux modèles / modes sur la même vidéo
- [ ] Installeurs « un clic » : script Windows (.ps1) et Linux/macOS (.sh) qui installent uv, Python 3.14,
      PyTorch adapté au matériel détecté, puis ouvrent l'interface

## 2. Projets à intégrer et maintenir à jour

- [ ] Fiche « ajouter un projet » (`docs/projet/nouveau-projet.md`) : structure, registre `projets/__init__.py`,
      prérequis, tests, mise à jour vers les dernières versions
- [ ] Football : moderniser (sources live, statistiques : possession, position du ballon en mètres,
      distances parcourues, événements `possession_change`) ; réentraîner les 3 modèles en **YOLO26** sur
      les jeux Roboflow Universe (football-players, ball, pitch keypoints)
- [ ] Projet « objets statiques » séparé ou mode dédié (aujourd'hui dans `distance_vitesse --select-static`)
- [ ] Autres projets Ultralytics / Roboflow / communauté : sport (basket, tennis), comptage d'animaux,
      parking intelligent, sécurité (intrusion, objet abandonné), retail (files d'attente)
- [ ] Veille automatique : Dependabot + job hebdomadaire qui teste le labo sur la dernière version
      d'Ultralytics/supervision et ouvre une issue en cas de casse

## 3. Assistance à la création de modèles

- [ ] Annotation assistée (pré-annotation par YOLOE/SAM 2, correction dans l'interface)
- [ ] Entraînement guidé (choix du modèle selon le matériel, suivi, export) ; import Roboflow Universe
- [ ] Assistant IA : explique les résultats, propose des réglages, aide à écrire les zones/intégrations
- [ ] Évaluation : métriques, comparaison avant/après sur les vidéos du labo

## 4. Projet distance_vitesse

- [ ] Valider YOLOE de bout en bout (`pip install git+https://github.com/ultralytics/CLIP.git`)
- [ ] Ré-identification (ReID) : moins de changements d'identifiant (faux `zone_exit` sur les voitures garées)
- [ ] Plaques : Corse `2A`/`2B`, collection, `W garage` ; formats Allemagne, Suisse, Pays-Bas, Portugal
- [ ] Vitesse : filtre de Kalman ; alertes d'excès de vitesse par zone (calibration obligatoire)
- [ ] Distance entre objets, temps de stationnement, trajectoires, cartes de chaleur
- [ ] Regroupement personne + objet étendu : cavalier, poussette, trottinette
- [ ] Réduire la complexité de `Pipeline._run_video`, `RiderGrouper.apply` (Sonar)

## 5. Vidéo et intégrations

- [ ] Upscaling (Real-ESRGAN) des vidéos faibles, ou ciblé sur les recadrages de plaques
- [ ] Débruitage / nuit ; encodage H.264 de la vidéo enregistrée (au lieu de mp4v)
- [ ] Floutage automatique visages/plaques dans les exports (RGPD)
- [ ] Diffusion : SRT/WebRTC, plusieurs destinations, superposition d'un logo/score
- [ ] Sorties : base de données (PostgreSQL/InfluxDB), Grafana, Home Assistant (découverte MQTT), GPIO / Modbus
      pour piloter des équipements (barrière, feu, alarme)
- [ ] Rapports périodiques (CSV/JSON toutes les N minutes) pour les flux live

## 6. Production

- [ ] Export TensorRT / OpenVINO automatique au premier lancement
- [ ] Image Docker Jetson (ARM64) et image CPU publiées sur GHCR
- [ ] Tests d'intégration sur les vidéos d'exemple dans la CI (LFS)
- [ ] Documentation : migrer vers Zensical (Material for MkDocs en fin de vie en mai 2027)

## Fait (v0.2)

- [x] YOLO26, modes `fast` / `accurate`, `.env`, suivi, distance (hauteur), vitesse, calibration sol
- [x] Plaques multi-pays + formats France SIV/FNI ; zones et lignes ; cyclistes/motards ; animaux
- [x] Docker, MkDocs, échantillons libres de droits (LFS), tests, CI
