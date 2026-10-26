# Données de test

`scripts/download_samples.py` télécharge des vidéos **sous licence libre** depuis Wikimedia Commons, les
découpe (30 s maximum), les réencode en H.264 sans son, et écrit les crédits dans `samples/SOURCES.md`.

```bash
python scripts/download_samples.py          # ffmpeg recommandé (sinon copie des .webm d'origine)
python scripts/download_samples.py --force  # tout retélécharger
```

| Fichier | Scène | Cas d'usage | Licence |
|---|---|---|---|
| `videos/street_ljubljana.mp4` | Rue piétonne, Slovénie | Distance, vitesse, plaques UE, cyclistes | CC BY 3.0 |
| `videos/parking_cctv.mp4` | Vraie caméra de surveillance de parking | Mode CCTV, zones, plaques | Domaine public |
| `videos/crosswalk_toronto.mp4` | Carrefour très fréquenté | Foule, lignes de passage | CC0 |
| `videos/roundabout.mp4` | Rond-point filmé par drone | Petits objets, comptage | CC0 |
| `videos/dogs_tokyo.mp4` | Promeneur de chiens | Animaux | CC BY-SA 4.0 |
| `images/plate_test.png` | Plaque tchèque | Test de l'OCR | MIT (fast-alpr) |

!!! note "Attribution"
    Les licences CC BY et CC BY-SA imposent de créditer les auteurs : `samples/SOURCES.md` doit accompagner
    les fichiers. La vidéo `dogs_tokyo.mp4` modifiée reste sous CC BY-SA 4.0.

## Faut-il commiter les échantillons ?

Les vidéos découpées pèsent ~44 Mo au total. Le dépôt est configuré pour les stocker avec **Git LFS**
(`.gitattributes`) :

| Option | Avantages | Inconvénients |
|---|---|---|
| Commiter via LFS | Clone prêt à l'emploi, CI possible sur les vidéos | Quota LFS GitHub (stockage et bande passante limités en gratuit) |
| Ne pas commiter | Dépôt léger | Chaque utilisateur lance le script (~230 Mo à télécharger avant découpe) |

```bash
git lfs install
git add samples/
git lfs ls-files     # vérifier que les .mp4 passent bien par LFS
```

## Flux en direct pour tester le mode `fast`

- Webcam : `SOURCE=0`
- Caméra IP du réseau local : `rtsp://…`
- Simuler une caméra à partir d'un fichier (serveur RTSP local, ex. [MediaMTX](https://github.com/bluenviron/mediamtx)) :

    ```bash
    ffmpeg -re -stream_loop -1 -i samples/videos/parking_cctv.mp4 -c copy -f rtsp rtsp://localhost:8554/parking
    python -m vision_lab distance_vitesse rtsp://localhost:8554/parking --mode fast
    ```

Les webcams publiques (YouTube Live, sites de villes) ont des conditions d'utilisation variables :
vérifiez-les avant de les enregistrer ou de les analyser.
