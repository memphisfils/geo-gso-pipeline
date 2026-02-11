# 🚀 GEO/GSO Pipeline — Article Generation & Scoring

Pipeline CLI Python qui génère automatiquement des articles **GEO-ready** (optimisés pour les moteurs de recherche génératifs type ChatGPT, Gemini, Perplexity), avec scoring qualité, anti-duplication et export publication-ready.

## 📦 Installation

```bash
# Cloner le repo
git clone <repo-url>
cd geo-gso-pipeline

# Créer un environnement virtuel (recommandé)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Installer les dépendances
pip install -r requirements.txt

# Configurer les secrets
cp .env.example .env
# Éditer .env et ajouter votre clé OPENAI_API_KEY
```

## ▶️ Exécution

```bash
# Lancement standard
python generate.py --input topics.json --output ./out

# Avec traitement parallèle (bonus)
python generate.py --input topics.json --output ./out --parallel
```

### Output

Le dossier `./out` contiendra :

```
out/
├── articles/    # 1 fichier .md par article (Markdown)
├── json/        # 1 fichier .json par article (publication-ready)
├── html/        # 1 fichier .html par article (avec SEO meta tags)
└── summary.json # Rapport global (scores, duplicates, erreurs)
```

## 🏗️ Architecture

```
geo-gso-pipeline/
├── generate.py              # CLI entrypoint (orchestration)
├── topics.json              # Input : 10 sujets (fr/en)
├── requirements.txt         # Dépendances Python
├── .env.example             # Template des variables d'environnement
├── src/
│   ├── config.py            # Configuration & chargement .env
│   ├── llm_client.py        # Client OpenAI + retries/backoff
│   ├── article_generator.py # Génération structurée GEO + validation
│   ├── scorer.py            # Scoring qualité (5 critères, /100)
│   ├── deduplication.py     # Anti-duplication par embeddings
│   └── exporter.py          # Export MD/JSON/HTML + summary
└── out/                     # Output généré
```

## 🔧 Choix Techniques

### LLM : OpenAI GPT-4o
- **Pourquoi** : Meilleur rapport qualité/coût pour la génération d'articles structurés longs
- **Retries** : Backoff exponentiel (2s/4s/8s) sur `RateLimitError`, `APITimeoutError`, `APIConnectionError`
- **Prompt engineering** : Prompt système + utilisateur en 2 étapes avec format obligatoire strict

### Scoring : 5 critères (/20 chacun → total /100)

| Critère | Ce qui est mesuré |
|---------|-------------------|
| **Structure** | Présence des 8 sections obligatoires (H1, meta, intro, TOC, corps, FAQ, takeaways, sources, auteur) |
| **Lisibilité** | Score Flesch via `textstat` + analyse des listes et du formatage |
| **Sources** | Nombre ≥ 3 + diversité des domaines |
| **LLM-friendliness** | Réponses directes, listes, FAQ, densité d'info, entités |
| **Risque duplication** | Score de similarité cosinus max avec les autres articles |

### Anti-duplication : Embeddings + Cosine Similarity
- **Modèle** : `sentence-transformers/all-MiniLM-L6-v2` (exécution locale, pas d'appel API)
- **Méthode** : Cosine similarity via `sklearn.metrics.pairwise`
- **Seuil** : Configurable (défaut: 0.85). Au-delà → rejet avec warning
- **Avantage** : Détection sémantique (pas juste lexicale), résistant à la paraphrase

### Export
- **Markdown** : Article complet prêt à publier
- **JSON** : Schéma structuré avec slug, meta, FAQ, scores, auteur
- **HTML (bonus)** : Page autonome avec `og:title`, `og:description`, Twitter Cards, CSS intégré

## ⚠️ Limites & Améliorations Proposées

### Limites actuelles
- **Sources** : Les URLs générées par le LLM sont plausibles mais pas vérifiées. Un module de fact-checking serait nécessaire en production
- **Volume** : Le pipeline séquentiel est limité par le rate limit de l'API OpenAI (~10 articles/run)
- **Validation** : La détection des sections est basée sur des regex, ce qui peut être fragile face à des formats markdown inhabituels

### Améliorations pour le scaling
- **Queue / Workers** : Intégrer Celery ou Redis Queue pour le batch processing asynchrone
- **CMS Integration** : Publication automatique via WordPress REST API ou headless CMS (Strapi, Contentful)
- **Monitoring** : Dashboard Grafana pour suivre les scores, le coût API, le throughput
- **RAG** : Module Retrieval-Augmented Generation pour citer des sources réelles depuis une base documentaire
- **Source Verification** : Scraping + vérification des URLs de sources générées
- **Multi-LLM** : Fallback automatique entre OpenAI → Anthropic → Mistral
- **Cache** : Mise en cache des embeddings pour accélérer la déduplication sur les runs successifs

## 📄 Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `OPENAI_API_KEY` | Clé API OpenAI (obligatoire) | — |
| `LLM_MODEL` | Modèle LLM à utiliser | `gpt-4o` |
| `SIMILARITY_THRESHOLD` | Seuil de similarité pour la déduplication | `0.85` |
| `MAX_RETRIES` | Nombre max de retries API | `3` |
| `REQUEST_TIMEOUT` | Timeout API en secondes | `90` |

## 📋 Licence

MIT
