"""
Mock LLM Client for testing without API costs.
Generates realistic fake articles for demonstration and testing.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MockLLMClient:
    """
    Mock LLM client that generates fake articles without API calls.
    
    Features:
    - Generates structurally valid articles
    - No API costs
    - Instant execution
    - Useful for testing and demos
    """
    
    def __init__(self, api_key: str = "mock", model: str = "mock-model"):
        self.api_key = api_key
        self.model = model
        logger.info("Initialized MockLLMClient (no API calls will be made)")
    
    def generate_article(
        self, 
        topic: str, 
        language: str, 
        tone: str, 
        additional_context: str = ""
    ) -> str:
        """
        Generate a mock article with proper GEO/GSO structure.
        
        Args:
            topic: Article topic
            language: Target language ('en' or 'fr')
            tone: Writing tone
            additional_context: Additional context (ignored in mock)
            
        Returns:
            Properly structured markdown article
        """
        logger.info(f"[MOCK] Generating article for: {topic} ({language}, {tone})")
        
        if language == "fr":
            return self._generate_french(topic, tone)
        else:
            return self._generate_english(topic, tone)
    
    def _generate_english(self, topic: str, tone: str) -> str:
        """Generate English article."""
        return f"""# {topic}: Complete Guide 2026

**Meta description:** Discover everything you need to know about {topic.lower()} in this comprehensive guide. Expert insights, practical tips, and real-world examples included here for you.

## Introduction
[3-5 lines maximum. Hook the reader, state the problem, preview the solution.]

This is a demonstration article about {topic}. In this comprehensive guide, we'll explore the key aspects, best practices, and actionable insights. This content is generated in demo mode for testing purposes.

## Table of Contents
[Auto-generated list of all H2 sections below]

## Understanding the Basics
[Informative content with H3 subsections if needed]

When it comes to {topic.lower()}, understanding the fundamentals is crucial. Here are the core concepts:

- **Definition**: What exactly is {topic.lower()} and why it matters
- **Key Components**: The essential elements you need to know
- **Historical Context**: How we got here and where we're going

### Core Principles

The foundation of {topic.lower()} rests on several key principles:

1. **Principle 1**: Quality over quantity - focus on what matters
2. **Principle 2**: Consistency is key - maintain regular practices
3. **Principle 3**: Adapt and evolve - stay current with trends

## Key Considerations
[Informative content with H3 subsections if needed]

Before diving deeper into {topic.lower()}, consider these important factors:

### Budget Considerations

- **Entry Level**: $0-100/month (getting started)
- **Mid-Range**: $100-500/month (established users)
- **Enterprise**: $500+/month (advanced implementations)

### Time Investment

Expect to invest approximately:
- Setup: 2-4 hours
- Learning curve: 1-2 weeks
- Ongoing maintenance: 2-4 hours/week

### Technical Requirements

- No special technical skills required
- Basic understanding helpful
- Support resources available

## Best Practices and Strategies
[Informative content with H3 subsections if needed]

Here are proven strategies for success with {topic.lower()}:

### Strategy 1: Start Small, Scale Smart

Begin with the basics and gradually expand. This approach minimizes risk while maximizing learning.

**Key Actions:**
- Set clear, measurable goals
- Track progress consistently
- Adjust based on results

### Strategy 2: Focus on Quality

Quality always trumps quantity. Better to do fewer things well than many things poorly.

### Strategy 3: Learn from Others

Study successful case studies and adapt proven methods to your context.

## Common Pitfalls to Avoid
[Informative content with H3 subsections if needed]

Avoid these common mistakes when working with {topic.lower()}:

- ❌ **Rushing the process** - Take time to plan properly
- ❌ **Ignoring best practices** - Follow established guidelines
- ❌ **Neglecting maintenance** - Regular upkeep is essential
- ❌ **Overlooking details** - Small things make big differences
- ❌ **Failing to measure** - Track your results consistently

## Implementation Guide
[Informative content with H3 subsections if needed]

Ready to implement {topic.lower()}? Follow this step-by-step guide:

### Step 1: Planning Phase

Define your objectives, timeline, and success metrics.

### Step 2: Setup and Configuration

Gather necessary resources and configure your environment.

### Step 3: Initial Implementation

Start with a pilot or small-scale implementation.

### Step 4: Testing and Refinement

Test thoroughly and refine based on feedback.

### Step 5: Full Rollout

Scale up to full implementation once validated.

## FAQ

**Q: How long does it take to see results with {topic.lower()}?**
A: Most users see initial results within 2-4 weeks, with significant improvements after 2-3 months of consistent application.

**Q: What is the typical cost involved?**
A: Costs vary widely depending on scale, ranging from free entry-level options to $500+/month for enterprise solutions.

**Q: Do I need special technical skills?**
A: No special technical skills are required. Basic computer literacy and willingness to learn are sufficient for most applications.

**Q: Can this work for small businesses?**
A: Absolutely! Many solutions are specifically designed for small business needs with scaled pricing and features.

**Q: What are the most common mistakes to avoid?**
A: The most common mistakes are rushing the implementation, neglecting planning, and failing to track results consistently.

**Q: Is there a free trial available?**
A: Many providers offer free trials or free tiers. Check specific provider offerings for details.

**Q: How often should I review and update my approach?**
A: Review monthly and make adjustments as needed. Quarterly deep reviews are recommended for strategy refinement.

## Key Takeaways

- Understanding fundamentals is crucial before implementation
- Start small and scale based on validated results
- Quality and consistency matter more than speed
- Avoid common pitfalls by learning from others
- Regular measurement and adjustment are essential
- Budget varies widely based on needs and scale
- Technical barriers are minimal for most users

## Sources

1. [Industry Standards Guide](https://example.com/standards-2026) — Comprehensive overview of current best practices
2. [Research Report 2026](https://example.com/research-report) — Latest data and trends analysis
3. [Expert Insights Database](https://example.com/expert-insights) — Curated expert opinions and case studies

---

**About the Author**

**Demo Expert** — Content Generation Specialist

Demo Expert is a fictional expert created for testing purposes. This bio demonstrates proper formatting and structure for author sections in generated articles.

**Methodology:**
- Mock generation for testing purposes
- Structural validation and compliance checking
- Fast execution without API costs
"""

    def _generate_french(self, topic: str, tone: str) -> str:
        """Generate French article."""
        return f"""# {topic} : Guide Complet 2026

**Meta description:** Découvrez tout ce qu'il faut savoir sur {topic.lower()} dans ce guide complet. Conseils d'experts, astuces pratiques et exemples concrets inclus ici pour vous.

## Introduction
[3-5 lines maximum. Hook the reader, state the problem, preview the solution.]

Ceci est un article de démonstration sur {topic}. Dans ce guide complet, nous explorerons les aspects clés, les meilleures pratiques et les insights actionnables. Ce contenu est généré en mode démo à des fins de test.

## Table des Matières
[Auto-generated list of all H2 sections below]

## Comprendre les Bases
[Informative content with H3 subsections if needed]

Lorsqu'il s'agit de {topic.lower()}, comprendre les fondamentaux est crucial. Voici les concepts de base :

- **Définition** : Qu'est-ce que {topic.lower()} exactement et pourquoi c'est important
- **Composants Clés** : Les éléments essentiels à connaître
- **Contexte Historique** : Comment nous en sommes arrivés là et où nous allons

### Principes Fondamentaux

Les bases de {topic.lower()} reposent sur plusieurs principes clés :

1. **Principe 1** : La qualité plutôt que la quantité - concentrez-vous sur l'essentiel
2. **Principe 2** : La cohérence est la clé - maintenez des pratiques régulières
3. **Principe 3** : Adaptez-vous et évoluez - restez à jour avec les tendances

## Considérations Clés
[Informative content with H3 subsections if needed]

Avant d'approfondir {topic.lower()}, considérez ces facteurs importants :

### Considérations Budgétaires

- **Niveau Débutant** : 0-100€/mois (pour commencer)
- **Niveau Intermédiaire** : 100-500€/mois (utilisateurs établis)
- **Entreprise** : 500€+/mois (implémentations avancées)

### Investissement en Temps

Prévoyez d'investir environ :
- Configuration : 2-4 heures
- Courbe d'apprentissage : 1-2 semaines
- Maintenance continue : 2-4 heures/semaine

### Exigences Techniques

- Aucune compétence technique spéciale requise
- Compréhension de base utile
- Ressources d'assistance disponibles

## Meilleures Pratiques et Stratégies
[Informative content with H3 subsections if needed]

Voici des stratégies éprouvées pour réussir avec {topic.lower()} :

### Stratégie 1 : Commencer Petit, Évoluer Intelligemment

Commencez par les bases et développez progressivement. Cette approche minimise les risques tout en maximisant l'apprentissage.

**Actions Clés :**
- Définir des objectifs clairs et mesurables
- Suivre les progrès de manière cohérente
- Ajuster en fonction des résultats

### Stratégie 2 : Privilégier la Qualité

La qualité prime toujours sur la quantité. Mieux vaut faire moins de choses bien que beaucoup de choses mal.

### Stratégie 3 : Apprendre des Autres

Étudiez les études de cas réussies et adaptez les méthodes éprouvées à votre contexte.

## Pièges Courants à Éviter
[Informative content with H3 subsections if needed]

Évitez ces erreurs courantes lors du travail avec {topic.lower()} :

- ❌ **Précipiter le processus** - Prenez le temps de bien planifier
- ❌ **Ignorer les meilleures pratiques** - Suivez les directives établies
- ❌ **Négliger la maintenance** - L'entretien régulier est essentiel
- ❌ **Négliger les détails** - Les petites choses font de grandes différences
- ❌ **Ne pas mesurer** - Suivez vos résultats de manière cohérente

## Guide de Mise en Œuvre
[Informative content with H3 subsections if needed]

Prêt à implémenter {topic.lower()} ? Suivez ce guide étape par étape :

### Étape 1 : Phase de Planification

Définissez vos objectifs, votre calendrier et vos métriques de succès.

### Étape 2 : Configuration et Setup

Rassemblez les ressources nécessaires et configurez votre environnement.

### Étape 3 : Implémentation Initiale

Commencez par un pilote ou une implémentation à petite échelle.

### Étape 4 : Tests et Raffinement

Testez minutieusement et affinez en fonction des retours.

### Étape 5 : Déploiement Complet

Passez à l'échelle une fois validé.

## FAQ

**Q: Combien de temps faut-il pour voir des résultats avec {topic.lower()} ?**
A: La plupart des utilisateurs voient des résultats initiaux dans les 2-4 semaines, avec des améliorations significatives après 2-3 mois d'application cohérente.

**Q: Quel est le coût typique impliqué ?**
A: Les coûts varient considérablement selon l'échelle, allant d'options gratuites pour débutants à 500€+/mois pour les solutions d'entreprise.

**Q: Ai-je besoin de compétences techniques spéciales ?**
A: Non, aucune compétence technique spéciale n'est requise. Une culture informatique de base et une volonté d'apprendre suffisent pour la plupart des applications.

**Q: Cela peut-il fonctionner pour les petites entreprises ?**
A: Absolument ! De nombreuses solutions sont spécifiquement conçues pour les besoins des petites entreprises avec des prix et fonctionnalités adaptés.

**Q: Quelles sont les erreurs les plus courantes à éviter ?**
A: Les erreurs les plus courantes sont de précipiter l'implémentation, de négliger la planification et de ne pas suivre les résultats de manière cohérente.

**Q: Y a-t-il un essai gratuit disponible ?**
A: De nombreux fournisseurs proposent des essais gratuits ou des versions gratuites. Vérifiez les offres spécifiques des fournisseurs pour plus de détails.

**Q: À quelle fréquence dois-je réviser et mettre à jour mon approche ?**
A: Révisez mensuellement et effectuez des ajustements selon les besoins. Des révisions approfondies trimestrielles sont recommandées pour affiner la stratégie.

## Points Clés à Retenir

- Comprendre les fondamentaux est crucial avant l'implémentation
- Commencer petit et évoluer en fonction des résultats validés
- La qualité et la cohérence comptent plus que la vitesse
- Éviter les pièges courants en apprenant des autres
- La mesure et l'ajustement réguliers sont essentiels
- Le budget varie considérablement selon les besoins et l'échelle
- Les barrières techniques sont minimes pour la plupart des utilisateurs

## Sources

1. [Guide des Standards de l'Industrie](https://exemple.fr/standards-2026) — Vue d'ensemble complète des meilleures pratiques actuelles
2. [Rapport de Recherche 2026](https://exemple.fr/rapport-recherche) — Dernières données et analyse des tendances
3. [Base de Données d'Insights Experts](https://exemple.fr/insights-experts) — Opinions d'experts et études de cas organisées

---

**À Propos de l'Auteur**

**Expert Démo** — Spécialiste en Génération de Contenu

Expert Démo est un expert fictif créé à des fins de test. Cette bio démontre le formatage et la structure appropriés pour les sections d'auteur dans les articles générés.

**Méthodologie :**
- Génération simulée à des fins de test
- Validation structurelle et vérification de conformité
- Exécution rapide sans coûts d'API
"""


# Convenience function for backward compatibility
def create_mock_client(*args, **kwargs):
    """Factory function to create mock LLM client."""
    return MockLLMClient(*args, **kwargs)
