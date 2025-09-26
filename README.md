# Computer Vision - Classification d'images Cats & Dogs

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![FAST Api](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Keras](https://img.shields.io/badge/Keras-%23D00000.svg?style=for-the-badge&logo=Keras&logoColor=white)](https://keras.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=for-the-badge)](CONTRIBUTING.md)

<div align="center">

<h3>Classification d'images avec Keras et exposition du modèle via Fast API</br></h3>

[Explore the docs](docs/)

</div>

---

## 📌 Introduction

Ce projet est à vocation pédagogique sur des thématiques IA et MLOps. Il permet de réaliser des tâches de Computer Vision et spécifiquement de la classification d'images par la reconnaissance de chats et de chiens.  
Il est composé de :

- Un modèle de computer vision développé avec Keras 3 selon une architecture CNN. Voir le tutoriel Keras ([lien](https://keras.io/examples/vision/image_classification_from_scratch/)).
- Un service API développé avec Fast API, qui permet notamment de réaliser les opérations d'inférence (i.e prédiction), sur la route `/api/predict`.
- Une application web minimaliste (templates Jinja2).
- Des tests automatisés minimalistes (pytest).
- Un pipeline CI/CD minimaliste (Github Action).

## 📁 Structure du projet

```txt
project-name/
├── .github/
│   ├── workflows/           # CI/CD pipelines
│   └── ISSUE_TEMPLATE/      # Templates d'issues
├── config/                  # Fichiers de configuration
├── data/
│   ├── raw/                 # Données brutes (gitignored)
│   ├── processed/           # Données traitées (gitignored)
│   └── external/            # Données externes/références
├── docker/                  # Dockerfiles et compose
├── docs/                    # Documentation
├── graphana/                # Export des dashboard Grafana 
├── notebooks/               # Jupyter notebooks pour exploration
├── requirements/            # Dépendances par environnement
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── scripts/                 # Scripts d'automatisation/déploiement
├── src/                     # Code source principal
│   ├── api/                 # APIs et services web
│   ├── data/                # Scripts de traitement des données
│   ├── models/              # Modèles ML/IA
│   ├── monitoring/          # Monitoring des modèles
│   ├── utils/               # Utilitaires partagés
│   └── web/                 # Templates jinja2
├── tests/                   # Tests unitaires et d'intégration
├── .env.example             # Variables d'environnement exemple
├── .gitignore
├── README.md
├── Makefile                 # Commandes fréquentes
└── pyproject.toml           # Configuration Python/packaging
```

## 🛠️ Procédure d'installation

### Configuration des identifiants de connections

L'ensemble des données de connections sont déclarés dans un fichier `.env` à  la racine du projet. La structure à suivre est :

```bash
# Database connection settings

POSTGRES_DBNM=***
POSTGRES_USER=***
POSTGRES_PASS=***
POSTGRES_PORT=***

# Graphana connection settings
GRAFANA_ADMIN_PASSWORD=***
GRAFANA_PORT=***
```

Avant de procéder à toute étapes d'installation, *python@3.11+*, *docker* et l'utilitaire *make* doivent être installé. Toute les commandes nécessaires à la création de l'environement virtuel, au lancement de l'api et des services (Postgres, Grafana), création des tables SQL et tests automatisés sont décrites dans cette section.

```bash
make env           # Installer les dépendances dans un environnement virtuel

make up/down       # Lancement/arrêt des conteneurs docker pour la base Postgres et Grafana

make test          # Lancement des tests automatisés

make create-tables # Creation des tables dans la base Postgres

make drop-tables   # Suppression des tables dans la base Postgres

make start         # Lancement de l'API exposant le service de classification
```

## 🎯 API

Lorsque l'environnement virtuel est activé, vous pouvez lancer le serveur de l'API ...

```bash
python scripts/run_api.py
```

... et visiter la page de documentation Swagger :

![Swagger](/docs/img/swagger.png "Page de documentation de l'API")

## 📊 Application web

Lorsque l'environnement virtuel est activé, vous pouvez lancer le serveur de l'API ...

```bash
python scripts/run_api.py
```

... et utiliser l'application web :

![Web APP](/docs/img/web.png "Application web du projet")

## 📄 Licence

MIT - voir LICENSE pour plus de détails.
