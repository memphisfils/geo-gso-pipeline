"""
RAG (Retrieval-Augmented Generation) module for the GEO/GSO Pipeline.
Enables citation from a document knowledge base.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Represents a document in the knowledge base."""
    id: str
    title: str
    content: str
    source: str
    metadata: Dict = field(default_factory=dict)


@dataclass
class RetrievedContext:
    """Result of RAG retrieval."""
    query: str
    documents: List[Document]
    scores: List[float]
    formatted_context: str


class SimpleVectorStore:
    """
    Simple in-memory vector store using sentence-transformers.
    No external database required.
    """
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector store.
        
        Args:
            embedding_model: Name of the sentence-transformers model.
        """
        self.embedding_model = embedding_model
        self.documents: List[Document] = []
        self.embeddings = None
        self._model = None
    
    def _get_model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.embedding_model}")
            self._model = SentenceTransformer(self.embedding_model)
        return self._model
    
    def add_documents(self, documents: List[Document]):
        """
        Add documents to the store.
        
        Args:
            documents: List of Document objects.
        """
        self.documents.extend(documents)
        
        # Generate embeddings for new documents
        model = self._get_model()
        texts = [f"{d.title}\n{d.content}" for d in documents]
        new_embeddings = model.encode(texts, show_progress_bar=False)
        
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            import numpy as np
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        
        logger.info(f"Added {len(documents)} documents to vector store")
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[Document, float]]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query.
            top_k: Number of results.
            
        Returns:
            List of (Document, score) tuples.
        """
        if len(self.documents) == 0:
            return []
        
        model = self._get_model()
        query_embedding = model.encode([query], show_progress_bar=False)
        
        # Compute cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top-k indices
        import numpy as np
        # Handle case where we have fewer docs than top_k
        k = min(top_k, len(self.documents))
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append((self.documents[idx], float(similarities[idx])))
        
        return results


class KnowledgeBase:
    """
    Knowledge base manager for RAG.
    Handles document loading, indexing, and retrieval.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the knowledge base.
        
        Args:
            data_dir: Directory containing knowledge base documents.
        """
        self.data_dir = Path(data_dir) if data_dir else None
        self.vector_store = SimpleVectorStore()
        self.is_loaded = False
    
    def load_from_directory(self, directory: str = None):
        """
        Load documents from a directory.
        
        Supports: .txt, .md, .json
        
        Args:
            directory: Path to documents directory.
        """
        dir_path = Path(directory or self.data_dir)
        
        if not dir_path.exists():
            logger.warning(f"Knowledge base directory not found: {dir_path}")
            return
        
        documents = []
        
        for file_path in dir_path.rglob("*"):
            if file_path.suffix == ".txt":
                doc = self._load_text_file(file_path)
                documents.append(doc)
            elif file_path.suffix == ".md":
                doc = self._load_markdown_file(file_path)
                documents.append(doc)
            elif file_path.suffix == ".json":
                docs = self._load_json_file(file_path)
                documents.extend(docs)
        
        if documents:
            self.vector_store.add_documents(documents)
            self.is_loaded = True
            logger.info(f"Loaded {len(documents)} documents into knowledge base")
    
    def _load_text_file(self, file_path: Path) -> Document:
        """Load a plain text file."""
        content = file_path.read_text(encoding="utf-8")
        return Document(
            id=str(file_path),
            title=file_path.stem,
            content=content,
            source=str(file_path),
            metadata={"type": "text", "filename": file_path.name},
        )
    
    def _load_markdown_file(self, file_path: Path) -> Document:
        """Load a markdown file."""
        content = file_path.read_text(encoding="utf-8")
        # Extract title from first H1
        import re
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem
        
        return Document(
            id=str(file_path),
            title=title,
            content=content,
            source=str(file_path),
            metadata={"type": "markdown", "filename": file_path.name},
        )
    
    def _load_json_file(self, file_path: Path) -> List[Document]:
        """Load a JSON file (array of documents)."""
        documents = []
        
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            
            if isinstance(data, list):
                for i, item in enumerate(data):
                    documents.append(Document(
                        id=item.get("id", f"{file_path}_{i}"),
                        title=item.get("title", f"Document {i}"),
                        content=item.get("content", ""),
                        source=item.get("source", str(file_path)),
                        metadata=item.get("metadata", {}),
                    ))
            elif isinstance(data, dict):
                documents.append(Document(
                    id=data.get("id", str(file_path)),
                    title=data.get("title", file_path.stem),
                    content=data.get("content", ""),
                    source=data.get("source", str(file_path)),
                    metadata=data.get("metadata", {}),
                ))
        except Exception as e:
            logger.error(f"Failed to load JSON {file_path}: {e}")
        
        return documents
    
    def create_sample_knowledge_base(self, output_dir: str):
        """
        Create a sample knowledge base for testing.
        
        Args:
            output_dir: Directory to save sample documents.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Sample documents for different topics
        sample_docs = [
            {
                "id": "whey_protein_guide",
                "title": "Complete Guide to Whey Protein",
                "content": """
# Complete Guide to Whey Protein

Whey protein is a high-quality protein derived from milk during the cheese-making process. It contains all nine essential amino acids and is rapidly absorbed by the body.

## Types of Whey Protein

1. **Whey Concentrate**: 70-80% protein, contains some lactose and fat
2. **Whey Isolate**: 90%+ protein, minimal lactose and fat
3. **Whey Hydrolysate**: Pre-digested for faster absorption

## Benefits for Athletes

- Muscle protein synthesis
- Recovery enhancement
- Immune system support
- Satiety promotion

## Recommended Daily Intake

Research suggests 1.6-2.2g of protein per kg of body weight for athletes engaged in resistance training.

**Sources:**
- Journal of the International Society of Sports Nutrition
- American College of Sports Medicine guidelines
                """,
                "source": "Internal knowledge base",
                "metadata": {"category": "nutrition", "tags": ["protein", "fitness"]}
            },
            {
                "id": "crm_selection_guide",
                "title": "CRM Selection Guide for SMBs",
                "content": """
# CRM Selection Guide for Small and Medium Businesses

Choosing the right CRM (Customer Relationship Management) system is crucial for business growth. This guide covers key considerations for SMBs.

## Key Features to Evaluate

1. **Contact Management**: Centralized customer data
2. **Sales Pipeline**: Visual deal tracking
3. **Automation**: Workflow and task automation
4. **Integration**: Connect with existing tools
5. **Reporting**: Analytics and insights

## Top CRM Options for SMBs (2024-2025)

| CRM | Best For | Price Range |
|-----|----------|-------------|
| HubSpot | All-in-one | Free-$800/mo |
| Salesforce Essentials | Scalability | $25/user/mo |
| Pipedrive | Sales-focused | $15-$99/user/mo |
| Zoho CRM | Value | $14-$52/user/mo |

## Implementation Best Practices

- Start with core features
- Train team thoroughly
- Migrate data carefully
- Set clear KPIs
                """,
                "source": "Internal knowledge base",
                "metadata": {"category": "business", "tags": ["crm", "smb", "software"]}
            },
            {
                "id": "ai_productivity_tools",
                "title": "AI Tools for Productivity in 2025",
                "content": """
# AI Tools for Productivity in 2025

Artificial Intelligence has transformed personal and professional productivity. Here are the top tools and their applications.

## Categories of AI Productivity Tools

### Writing & Content
- **ChatGPT/Claude**: Content generation, editing
- **Jasper**: Marketing copy
- **Grammarly**: Writing enhancement

### Task Management
- **Notion AI**: Document management
- **Motion**: Calendar optimization
- **Reclaim.ai**: Time blocking

### Research & Analysis
- **Perplexity**: AI-powered search
- **Elicit**: Academic research
- **Consensus**: Scientific literature

## ROI Considerations

Studies show AI productivity tools can save 2-3 hours daily for knowledge workers when properly implemented.

## Selection Criteria

1. Integration capabilities
2. Data privacy compliance
3. Learning curve
4. Pricing model
5. Support quality
                """,
                "source": "Internal knowledge base",
                "metadata": {"category": "technology", "tags": ["ai", "productivity", "tools"]}
            }
        ]
        
        # Save as JSON
        output_file = output_path / "knowledge_base.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(sample_docs, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created sample knowledge base at: {output_file}")
    
    def retrieve(self, query: str, top_k: int = 3) -> RetrievedContext:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: The search query.
            top_k: Number of documents to retrieve.
            
        Returns:
            RetrievedContext with documents and formatted text.
        """
        results = self.vector_store.search(query, top_k)
        
        documents = []
        scores = []
        
        for doc, score in results:
            documents.append(doc)
            scores.append(score)
        
        # Format context for LLM
        formatted = self._format_context(documents, scores)
        
        return RetrievedContext(
            query=query,
            documents=documents,
            scores=scores,
            formatted_context=formatted,
        )
    
    def _format_context(self, documents: List[Document], scores: List[float]) -> str:
        """Format retrieved documents for LLM context."""
        if not documents:
            return "No relevant context found."
        
        parts = ["## Retrieved Context\n"]
        
        for i, (doc, score) in enumerate(zip(documents, scores), 1):
            parts.append(f"### Source {i}: {doc.title} (relevance: {score:.2f})")
            parts.append(f"Source: {doc.source}")
            parts.append(f"Content:\n{doc.content[:500]}...")
            parts.append("")
        
        return "\n".join(parts)


class RAGEnricher:
    """
    Enriches articles with RAG-retrieved context.
    """
    
    def __init__(self, knowledge_base: KnowledgeBase):
        self.kb = knowledge_base
    
    def enrich_prompt(self, topic: str, base_prompt: str) -> str:
        """
        Enrich a generation prompt with retrieved context.
        
        Args:
            topic: The article topic.
            base_prompt: The original prompt.
            
        Returns:
            Enriched prompt with context.
        """
        context = self.kb.retrieve(topic, top_k=2)
        
        enrichment = f"""
{context.formatted_context}

---

Use the above context to enrich your article with accurate information and cite the sources when relevant.

{base_prompt}
"""
        return enrichment
    
    def get_citations_for_topic(self, topic: str) -> List[Dict]:
        """
        Get citation-ready references for a topic.
        
        Args:
            topic: The article topic.
            
        Returns:
            List of citation dictionaries.
        """
        context = self.kb.retrieve(topic, top_k=3)
        
        citations = []
        for doc, score in zip(context.documents, context.scores):
            citations.append({
                "title": doc.title,
                "source": doc.source,
                "relevance": round(score, 3),
                "type": doc.metadata.get("type", "document"),
            })
        
        return citations


def create_rag_enhanced_generator(knowledge_base_dir: str = None):
    """
    Factory function to create a RAG-enhanced article generator.
    
    Args:
        knowledge_base_dir: Directory containing knowledge base.
        
    Returns:
        Configured RAGEnricher instance.
    """
    kb = KnowledgeBase(knowledge_base_dir)
    
    if knowledge_base_dir and os.path.exists(knowledge_base_dir):
        kb.load_from_directory()
    else:
        # Create sample knowledge base in 'data' dir relative to project root
        project_root = Path(os.path.dirname(__file__)).parent
        sample_dir = project_root / "data" / "knowledge_base"
        kb.create_sample_knowledge_base(str(sample_dir))
        kb.load_from_directory(str(sample_dir))
    
    return RAGEnricher(kb)
