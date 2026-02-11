# 🚀 GEO/GSO Pipeline — Article Generation & Scoring

Pipeline CLI Python qui génère automatiquement des articles **GEO-ready** (optimisés pour les moteurs de recherche génératifs type ChatGPT, Gemini, Perplexity), avec scoring qualité, anti-duplication et export publication-ready.

## 🏗️ Architecture Complète

```mermaid
graph TD
    subgraph Input
        A[topics.json]
    end
    
    subgraph Generation
        B[ArticleGenerator]
        C[LLM Client - GPT-4o]
        D[RAG Module]
        E[Sources Retrieval]
    end
    
    subgraph Processing
        F[ArticleScorer]
        G[DeduplicationEngine]
    end
    
    subgraph Export
        H[ArticleExporter]
        I[WordPress Publisher]
    end
    
    subgraph Output
        J[/out/articles/*.md]
        K[/out/json/*.json]
        L[/out/html/*.html]
        M[WordPress Posts]
    end
    
    A --> B
    B --> C
    D --> B
    E --> B
    B --> F
    B --> G
    F --> H
    G --> H
    H --> J
    H --> K
    H --> L
    H --> I
    I --> M
```

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

## 📊 Exemple d'Article Généré

### Exemple de Score
```json
{
  "slug": "meilleures-proteines-whey-en-2026",
  "score": {
    "total": 87,
    "details": {
      "structure": 18,
      "readability": 17,
      "sources": 16,
      "llm_friendliness": 18,
      "duplication": 18
    },
    "warnings": ["Meta description slightly long (165 chars)"]
  }
}
```

## 🔧 Fonctionnalités Avancées

### WordPress Publication
```bash
# Publier sur WordPress
python generate.py --input topics.json --output ./out --wordpress
```

### Batch Processing
```bash
# Traitement parallèle avec 5 workers
python generate.py --input topics.json --output ./out --batch --workers 5
```

### Sources Retrieval
```bash
# Récupération de sources réelles
python generate.py --input topics.json --output ./out --sources-retrieval
```

### RAG Enrichment
```bash
# Enrichissement RAG depuis la base de connaissances
python generate.py --input topics.json --output ./out --rag
```

## 🧪 Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## 📈 Performance Benchmarks

| Metric | Value |
|--------|-------|
| Avg generation time | ~15s/article |
| Total pipeline (10 articles) | ~3 min |
| Memory usage | ~500MB |

## 🔧 Choix Techniques

### LLM : OpenAI GPT-4o
- **Pourquoi** : Meilleur rapport qualité/coût pour la génération d'articles structurés longs
- **Retries** : Backoff exponentiel (2s/4s/8s) sur `RateLimitError`, `APITimeoutError`, `APIConnectionError`
- **Prompt engineering** : Prompt système + utilisateur en 2 étapes avec format obligatoire strict

### Scoring : 5 critères (/20 chacun → total /100)
- **Structure** : Présence des 8 sections obligatoires (H1, meta, intro, TOC, corps, FAQ, takeaways, sources, auteur)
- **Lisibilité** : Score Flesch via `textstat` + analyse des listes et du formatage
- **Sources** : Nombre ≥ 3 + diversité des domaines
- **LLM-friendliness** : Réponses directes, listes, FAQ, densité d'info, entités
- **Risque duplication** : Score de similarité cosinus max avec les autres articles

### Anti-duplication : Embeddings + Cosine Similarity
- **Modèle** : `sentence-transformers/all-MiniLM-L6-v2` (exécution locale, pas d'appel API)
- **Seuil** : Configurable (défaut: 0.85). Au-delà → rejet avec warning

## 📄 Variables d'Environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `OPENAI_API_KEY` | Clé API OpenAI (obligatoire) | — |
| `LLM_MODEL` | Modèle LLM à utiliser | `gpt-4o` |
| `SIMILARITY_THRESHOLD` | Seuil déduplication | `0.85` |
| `WP_URL` | URL WordPress REST API | — |
| `WP_USERNAME` | Utilisateur WordPress | — |
| `WP_APP_PASSWORD` | Mot de passe application WP | — |
| `SERPER_API_KEY` | Clé API Serper (optionnelle) | — |
| `TAVILY_API_KEY` | Clé API Tavily (optionnelle) | — |

## 📋 Licence

MIT
