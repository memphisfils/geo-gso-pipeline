"""
LLM Client module for the GEO/GSO Pipeline.
Wraps OpenAI API with retry logic, exponential backoff, and error handling.
"""

import time
import logging
from openai import OpenAI, RateLimitError, APIConnectionError, APITimeoutError, APIError
from src.config import OPENAI_API_KEY, LLM_MODEL, REQUEST_TIMEOUT, MAX_RETRIES

logger = logging.getLogger(__name__)


class LLMClient:
    """OpenAI API client with production-grade error handling."""

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY, timeout=REQUEST_TIMEOUT)
        self.model = LLM_MODEL
        self.max_retries = MAX_RETRIES

    def _call_with_retry(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """
        Call the OpenAI API with exponential backoff retry logic.
        
        Args:
            messages: List of message dicts for the chat completion.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in the response.
            
        Returns:
            The content of the assistant's response.
            
        Raises:
            Exception: After all retries are exhausted.
        """
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"LLM API call (attempt {attempt}/{self.max_retries}) — model={self.model}")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                logger.info(f"LLM API call successful — {len(content)} chars returned")
                return content

            except RateLimitError as e:
                last_exception = e
                wait = 2 ** attempt
                logger.warning(f"Rate limit hit. Retrying in {wait}s... (attempt {attempt}/{self.max_retries})")
                time.sleep(wait)

            except APITimeoutError as e:
                last_exception = e
                wait = 2 ** attempt
                logger.warning(f"API timeout. Retrying in {wait}s... (attempt {attempt}/{self.max_retries})")
                time.sleep(wait)

            except APIConnectionError as e:
                last_exception = e
                wait = 2 ** attempt
                logger.warning(f"API connection error. Retrying in {wait}s... (attempt {attempt}/{self.max_retries})")
                time.sleep(wait)

            except APIError as e:
                last_exception = e
                logger.error(f"API error (non-retryable): {e}")
                raise

        logger.error(f"All {self.max_retries} retries exhausted.")
        raise last_exception

    def generate_article(self, topic: str, language: str, tone: str) -> str:
        """
        Generate a GEO-ready article for the given topic.
        
        Args:
            topic: The article subject.
            language: Target language ('fr' or 'en').
            tone: Writing tone ('expert', 'friendly', 'educational', 'analytical').
            
        Returns:
            The full article content in Markdown format.
        """
        lang_instruction = "en français" if language == "fr" else "in English"
        
        system_prompt = f"""You are an expert content writer specializing in GEO/GSO-optimized articles 
(articles optimized for generative AI search engines like ChatGPT, Gemini, Perplexity).

Your articles MUST be "LLM-friendly":
- Direct, structured answers (no fluff)
- Explicit entities (brands, concepts, categories)
- Short, scannable sections
- High information density
- Plausible citations/sources

Write {lang_instruction} with a {tone} tone."""

        user_prompt = f"""Generate a complete GEO-ready article about: "{topic}"

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
[Minimum 3 sources with plausible URLs]

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
5. Include AT LEAST 3 sources with plausible URLs
6. Meta description MUST be exactly 150-160 characters
7. Introduction MUST be 3-5 lines maximum
8. Content must be information-dense, no filler text
9. Use bullet points, numbered lists, and bold text for scannability
10. Include explicit entities (brand names, specific tools, metrics, prices when relevant)
"""

        return self._call_with_retry(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
