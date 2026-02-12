# 🚀 GEO/GSO Pipeline — The Ultimate Article Generator

> **"Transform simple topics into high-ranking, publication-ready articles optimized for the AI era (GEO/GSO/SEO) in seconds."**

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

An advanced, production-grade pipeline that generates, scores, and exports high-quality articles. Built for robustness, scalability, and extensibility.

---

## 👩‍💻 Guide pour le Correcteur (Evaluator Guide)

**Les résultats de l'exécution complète sont disponibles directement dans le dossier [`/out`](./out).**

Pour tester le pipeline immédiatement sans configuration complexe ni frais d'API, utilisez le **Mode Démo**.

```bash
# 1. Installation Rapide
./install.sh  # Linux/macOS
# OU
.\install.ps1 # Windows

# 2. Exécution Démo (Gratuit, Instantané, Sans Clé API)
source venv/bin/activate  # ou .\venv\Scripts\Activate.ps1
python generate.py --input topics_single.json --output ./out --demo
```

---

## 🏗️ Architecture System

Le pipeline suit une architecture modulaire et événementielle, conçue pour la fiabilité et la maintenabilité.

```mermaid
graph TD
    subgraph Inputs
        A[topics.json] -->|Load| B[CLI Controller]
    end

    subgraph Core Pipeline
        B -->|Orchestrate| C{Processing Mode}
        C -->|Sequential| D[ArticleGenerator]
        C -->|Parallel/Batch| D
        
        D -->|Prompt Engineering| E[LLM Client]
        E -->|API Call| F((LLM Providers))
        F -.->|OpenAI/Ant/Gemini/DeepSeek| E
        
        subgraph Enrichment
            D -.->|RAG| G[Vector Store]
            D -.->|Search| H[Web Sources]
        end
        
        D -->|Raw Text| I[Parser & Validator]
    end

    subgraph Quality Assurance
        I -->|Article Object| J[Deduplication Engine]
        J -->|Embeddings| K[Vector DB (Local)]
        J -->|Similarity Check| I
        
        I -->|Validated Article| L[Scorer]
        L -->|5-Criteria Analysis| M[Score Report]
    end

    subgraph Output & Publishing
        I -->|Export| N[Exporter]
        N --> O[Markdown / JSON / HTML]
        N -->|API| P[WordPress Publisher]
    end
```

---

## 🛠️ Manuel de Référence CLI (Command Line Interface)

Le script principal `generate.py` accepte de nombreux arguments pour personnaliser l'exécution.

### Usage de base
```bash
python generate.py --input <fichier_entree> [options]
```

### Liste complète des arguments
| Argument | Description | Exemple / Valeur |
|:---|:---|:---|
| `-h, --help` | Affiche l'aide et quitte. | `python generate.py --help` |
| `--input, -i` | **Obligatoire.** Chemin vers le fichier JSON des sujets. | `--input topics.json` |
| `--output, -o` | Dossier de sortie pour les articles et rapports. | `--output ./out` (Défaut: `./out`) |
| `--parallel` | Active le traitement parallèle (multithreading). | `python generate.py --input topics.json --parallel` |
| `--demo` | **Mode Démo.** Utilise un "Mock LLM" (gratuit, pas besoin d'API). | `python generate.py --input topics.json --demo` |
| `--provider` | Choix du fournisseur d'IA. | `openai`, `anthropic`, `gemini`, `deepseek` |
| `--model` | Nom spécifique du modèle. | `--model gpt-4o`, `--model claude-3-5-sonnet-20240620` |
| `--sources-retrieval` | Active la recherche de sources réelles sur le web. | `python generate.py --input topics.json --sources-retrieval` |
| `--rag` | Active l'enrichissement par base de connaissances locale. | `python generate.py --input topics.json --rag` |
| `--wordpress` | Publie automatiquement les articles sur WordPress. | `python generate.py --input topics.json --wordpress` |
| `--batch` | Active le mode Batch (Celery/Multiprocessing). | `python generate.py --input topics.json --batch` |
| `--workers` | Nombre de workers pour le mode Batch. | `--workers 5` (Défaut: 3) |

---

## ✨ Fonctionnalités Détaillées

### 🤖 Support Multi-LLM
Le pipeline est agnostique du fournisseur. Vous pouvez passer d'un modèle à l'autre simplement via la ligne de commande :
*   **OpenAI** (Par défaut) : `openai`
*   **Anthropic** : `anthropic` (Claude 3.5 Sonnet)
*   **Google** : `gemini` (Gemini 1.5 Pro)
*   **DeepSeek** : `deepseek` (Modèle DeepSeek-V3 via API compatible)

### 📊 Scoring de Qualité (/100)
Chaque article est noté selon 5 critères techniques (20 points chacun) :
1.  **Structure** : Respect des balises H1-H3, présence de la FAQ, meta, etc.
2.  **Lisibilité** : Score Flesch-Kincaid (ajusté pour le Français).
3.  **Sources** : Nombre et diversité des domaines cités.
4.  **LLM-friendliness** : Formatage optimisé pour être cité par les moteurs IA.
5.  **Risque de Duplication** : Score de similarité sémantique avec le reste du corpus.

### 🔍 Anti-Duplication Sémantique
Utilise des **Embeddings** (`all-MiniLM-L6-v2`) pour calculer la similarité cosinus entre les articles. Si deux sujets ou contenus sont trop proches (> 0.85), le pipeline lève une alerte.

### 🌐 Recherche Web & RAG
*   **Search Engine** : Capacité à chercher sur Google (via Serper/Tavily) ou DuckDuckGo pour sourcer des faits réels.
*   **RAG (Retrieval Augmented Generation)** : Injection de connaissances depuis vos propres documents locaux dans le prompt de génération.

---

## 🚀 Installation

### 1. Installation Automatique (Recommandé)
Les scripts d'installation gèrent la création du `venv`, la mise à jour de `pip`, et l'installation des dépendances.

**Linux/macOS :**
```bash
chmod +x install.sh
./install.sh
```

**Windows :**
```powershell
.\install.ps1
```

### 2. Docker
Le projet est entièrement containerisé avec support Redis pour les tâches asynchrones.
```bash
docker-compose up --build
```

---

## ⚙️ Configuration (.env)

| Variable | Description |
|:---|:---|
| `OPENAI_API_KEY` | Clé API pour OpenAI |
| `ANTHROPIC_API_KEY` | Clé API pour Anthropic |
| `GEMINI_API_KEY` | Clé API pour Google Gemini |
| `LLM_PROVIDER` | Fournisseur par défaut |
| `WP_URL` | URL de l'API WordPress |
| `WP_APP_PASSWORD` | Mot de passe d'application WordPress |

---

## 🧪 Tests & Qualité

```bash
# Lancer tous les tests
pytest tests/ -v

# Rapport de couverture
pytest tests/ --cov=src --cov-report=html
```

---

## 📄 Licence

MIT © 2026 Paul Fils Rasolo

