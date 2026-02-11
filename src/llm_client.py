"""
LLM Client module for the GEO/GSO Pipeline.
Supports multiple providers: OpenAI, Anthropic, Gemini, DeepSeek.
"""

import time
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional, List, Dict

from src.config import (
    OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, DEEPSEEK_API_KEY,
    LLM_MODEL, REQUEST_TIMEOUT, MAX_RETRIES, LLM_PROVIDER
)

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.max_retries = MAX_RETRIES

    @abstractmethod
    def generate_article(self, topic: str, language: str, tone: str, additional_context: str = "") -> str:
        """Generate an article using the specific provider."""
        pass

    def _build_system_prompt(self, language: str, tone: str, additional_context: str = "") -> str:
        """Helper to build the common system prompt."""
        lang_instruction = "en français" if language == "fr" else "in English"
        
        context_instruction = ""
        if additional_context:
            context_instruction = f"\n\nCONTEXT FROM KNOWLEDGE BASE / WEB SEARCH:\n{additional_context}\n\nUse this context to ensure accuracy and cite real sources where appropriate."
        
        return f"""You are an expert content writer specializing in GEO/GSO-optimized articles 
(articles optimized for generative AI search engines like ChatGPT, Gemini, Perplexity).

Your articles MUST be "LLM-friendly":
- Direct, structured answers (no fluff)
- Explicit entities (brands, concepts, categories)
- Short, scannable sections
- High information density
- Plausible citations/sources

{context_instruction}

Write {lang_instruction} with a {tone} tone."""

    def _build_user_prompt(self, topic: str) -> str:
        """Helper to build the common user prompt with structural requirements."""
        return f"""Generate a complete GEO-ready article about: "{topic}"

The article MUST follow this EXACT structure in Markdown:

# [Compelling H1 Title]

**Meta description:** [Exactly 150-160 characters, compelling summary]

## Introduction
[3-5 lines maximum. Hook the reader, state the problem, preview the solution.]

## Table of Contents
[Auto-generated list of all H2 sections below]

## [H2 Section 1 - Main Topic Area]
[Informative content with H3 subsections if needed]

## [H2 Section 2 - Another Key Area]
[Informative content with H3 subsections if needed]

## [H2 Section 3 - Comparison/Analysis]
[Informative content with H3 subsections if needed]

## [H2 Section 4 - Practical Advice]
[Informative content with H3 subsections if needed]

[You may add more H2 sections if relevant]

## FAQ

**Q: [Question 1]?**
A: [Direct, concise answer]

**Q: [Question 2]?**
A: [Direct, concise answer]

**Q: [Question 3]?**
A: [Direct, concise answer]

**Q: [Question 4]?**
A: [Direct, concise answer]

**Q: [Question 5]?**
A: [Direct, concise answer]

[Include more Q&A if relevant]

## Key Takeaways

- [Takeaway 1]
- [Takeaway 2]
- [Takeaway 3]
- [Takeaway 4]
- [Takeaway 5]
[5-8 bullet points total]

## Sources

1. [Source Name](https://plausible-url.com/path) — Brief description
2. [Source Name](https://plausible-url.com/path) — Brief description
3. [Source Name](https://plausible-url.com/path) — Brief description
[Minimum 3 sources with plausible URLs, or use real sources if provided in context]

---

**About the Author**

**[Fictional Expert Name]** — [Professional title]

[2-3 lines professional bio relevant to the topic]

**Methodology:**
- [How research was conducted]
- [What sources were analyzed]
- [How quality was ensured]

IMPORTANT RULES:
1. Every section listed above is MANDATORY
2. Use AT LEAST 4 H2 sections in the body (not counting FAQ, Takeaways, Sources)
3. FAQ must have AT LEAST 5 questions with direct answers
4. Key Takeaways must have 5-8 bullet points
5. Include AT LEAST 3 sources
6. Meta description MUST be exactly 150-160 characters
7. Introduction MUST be 3-5 lines maximum
8. Content must be information-dense, no filler text
9. Use bullet points, numbered lists, and bold text for scannability
10. Include explicit entities (brand names, specific tools, metrics, prices when relevant)
"""


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI API."""
    
    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model or "gpt-4o")
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, timeout=REQUEST_TIMEOUT)

    def generate_article(self, topic: str, language: str, tone: str, additional_context: str = "") -> str:
        from openai import RateLimitError, APIConnectionError, APITimeoutError, APIError
        
        system_prompt = self._build_system_prompt(language, tone, additional_context)
        user_prompt = self._build_user_prompt(topic)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"OpenAI Call (attempt {attempt}/{self.max_retries}) — model={self.model}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=4096,
                )
                return response.choices[0].message.content
            
            except (RateLimitError, APITimeoutError, APIConnectionError) as e:
                wait = 2 ** attempt
                logger.warning(f"OpenAI error: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            except Exception as e:
                logger.error(f"OpenAI fatal error: {e}")
                raise
        
        raise Exception("OpenAI retries exhausted")


class DeepSeekClient(OpenAIClient):
    """Client for DeepSeek (OpenAI-compatible)."""
    
    def __init__(self, api_key: str, model: str = None):
         # DeepSeek uses compatible API
        super().__init__(api_key, model or "deepseek-chat")
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key, 
            base_url="https://api.deepseek.com",
            timeout=REQUEST_TIMEOUT
        )


class AnthropicClient(BaseLLMClient):
    """Client for Anthropic (Claude)."""
    
    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model or "claude-3-5-sonnet-20240620")
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT)

    def generate_article(self, topic: str, language: str, tone: str, additional_context: str = "") -> str:
        import anthropic
        
        system_prompt = self._build_system_prompt(language, tone, additional_context)
        user_prompt = self._build_user_prompt(topic)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Anthropic Call (attempt {attempt}/{self.max_retries}) — model={self.model}")
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                return message.content[0].text
                
            except (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
                wait = 2 ** attempt
                logger.warning(f"Anthropic error: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            except Exception as e:
                logger.error(f"Anthropic fatal error: {e}")
                raise

        raise Exception("Anthropic retries exhausted")


class GeminiClient(BaseLLMClient):
    """Client for Google Gemini."""
    
    def __init__(self, api_key: str, model: str = None):
        super().__init__(api_key, model or "gemini-1.5-pro")
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model_name = self.model
        
    def generate_article(self, topic: str, language: str, tone: str, additional_context: str = "") -> str:
        import google.generativeai as genai
        from google.api_core import exceptions
        
        system_prompt = self._build_system_prompt(language, tone, additional_context)
        user_prompt = self._build_user_prompt(topic)
        
        # Gemini usually takes system instruction in model init or config
        model = genai.GenerativeModel(
            self.model_name,
            system_instruction=system_prompt
        )
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Gemini Call (attempt {attempt}/{self.max_retries}) — model={self.model_name}")
                response = model.generate_content(
                    user_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=8192,
                    )
                )
                return response.text
                
            except (exceptions.ResourceExhausted, exceptions.ServiceUnavailable) as e:
                wait = 2 ** attempt
                logger.warning(f"Gemini error: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            except Exception as e:
                logger.error(f"Gemini fatal error: {e}")
                raise

        raise Exception("Gemini retries exhausted")


class LLMClientFactory:
    """Factory to create LLM clients."""
    
    @staticmethod
    def create(provider: str = None, model: str = None) -> BaseLLMClient:
        provider = provider or LLM_PROVIDER
        provider = provider.lower()
        
        if provider == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not found")
            return OpenAIClient(OPENAI_API_KEY, model)
        
        elif provider == "anthropic":
            if not ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not found")
            return AnthropicClient(ANTHROPIC_API_KEY, model)
            
        elif provider == "gemini":
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not found")
            return GeminiClient(GEMINI_API_KEY, model)
            
        elif provider == "deepseek":
            if not DEEPSEEK_API_KEY:
                raise ValueError("DEEPSEEK_API_KEY not found")
            return DeepSeekClient(DEEPSEEK_API_KEY, model)
            
        else:
            raise ValueError(f"Unknown provider: {provider}")


# Facade for backward compatibility
class LLMClient:
    def __init__(self, provider: str = None, model: str = None):
        self.delegate = LLMClientFactory.create(provider, model)
    
    def generate_article(self, *args, **kwargs):
        return self.delegate.generate_article(*args, **kwargs)
