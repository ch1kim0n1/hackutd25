"""
Vocabulary Agent - Identifies financial jargon, terminology, and references in text.

This agent analyzes text output and extracts financial terms that need definitions.
It uses AI to intelligently identify terms that may be unclear to users.
"""

import os
import json
import logging
from typing import List, Dict, Any, Set
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VocabularyAgent:
    """
    Agent responsible for identifying financial terminology and jargon in text.
    """

    def __init__(self):
        """Initialize the Vocabulary Agent with AI client."""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.model = "nvidia/llama-3.1-nemotron-70b-instruct"

        # Common financial terms to always check for
        self.common_financial_terms = {
            'volatility', 'vix', 'spy', 'etf', 'allocation', 'diversification',
            'portfolio', 'drawdown', 'sharpe ratio', 'monte carlo', 'var',
            'value at risk', 'slippage', 'bull market', 'bear market',
            'liquidity', 'yield', 'dividend', 'market cap', 'beta', 'alpha',
            'correlation', 'hedge', 'derivative', 'options', 'futures',
            'bond', 'equity', 'asset', 'rebalancing', 'risk tolerance',
            'market order', 'limit order', 'stop loss', 'take profit',
            'momentum', 'trend', 'support', 'resistance', 'breakout',
            'consolidation', 'overbought', 'oversold', 'rsi', 'macd',
            'moving average', 'candlestick', 'bull', 'bear', 'sector',
            'index', 'benchmark', 'outperform', 'underperform', 'basis point',
            'inflation', 'deflation', 'fed', 'interest rate', 'quantitative easing',
            'tapering', 'fiscal policy', 'monetary policy', 'treasury',
            'corporate bond', 'municipal bond', 'credit rating', 'default',
            'maturity', 'coupon', 'par value', 'premium', 'discount'
        }

    def extract_financial_terms(self, text: str) -> Dict[str, Any]:
        """
        Extract financial terms from the given text using AI.

        Args:
            text: The text to analyze for financial terminology

        Returns:
            Dictionary containing:
            - terms: List of identified financial terms
            - references: Any specific references (companies, indices, etc.)
            - technical_terms: Highly technical terms that definitely need definitions
            - confidence: Confidence score of the extraction
        """
        logger.info("🔍 Vocabulary Agent: Extracting financial terms...")

        try:
            # Create prompt for AI to identify financial terms
            prompt = self._create_extraction_prompt(text)

            # Call AI model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial terminology expert. Extract and categorize financial terms from text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            # Parse AI response
            result = self._parse_extraction_response(response.choices[0].message.content)

            # Add simple pattern matching as backup
            simple_terms = self._simple_term_extraction(text)

            # Merge results
            result['terms'] = list(set(result.get('terms', []) + simple_terms))

            logger.info(f"✅ Vocabulary Agent: Found {len(result['terms'])} financial terms")
            return result

        except Exception as e:
            logger.error(f"❌ Vocabulary Agent error: {e}")
            # Fallback to simple extraction
            return {
                'terms': self._simple_term_extraction(text),
                'references': [],
                'technical_terms': [],
                'confidence': 0.5,
                'error': str(e)
            }

    def _create_extraction_prompt(self, text: str) -> str:
        """Create the prompt for AI to extract financial terms."""
        return f"""Analyze the following financial text and extract:

1. **Financial Terms**: Any financial jargon or terminology that a beginner might not understand
2. **References**: Specific references to companies, indices, or financial instruments (e.g., SPY, VIX, S&P 500)
3. **Technical Terms**: Highly technical terms that definitely need definitions (e.g., Sharpe ratio, Monte Carlo simulation)

Text to analyze:
\"\"\"
{text}
\"\"\"

Return your analysis in JSON format:
{{
    "terms": ["term1", "term2", ...],
    "references": ["SPY", "VIX", ...],
    "technical_terms": ["Sharpe ratio", "Monte Carlo", ...],
    "confidence": 0.0-1.0
}}

Only include terms that appear in the text. Use lowercase for terms (except proper nouns/acronyms).
"""

    def _parse_extraction_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response to extract structured data."""
        try:
            # Try to extract JSON from response
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = response_text.strip()

            result = json.loads(json_str)
            return result

        except Exception as e:
            logger.warning(f"Failed to parse AI response: {e}")
            return {
                'terms': [],
                'references': [],
                'technical_terms': [],
                'confidence': 0.3
            }

    def _simple_term_extraction(self, text: str) -> List[str]:
        """Simple pattern-based extraction as fallback."""
        text_lower = text.lower()
        found_terms = []

        for term in self.common_financial_terms:
            # Check if term appears in text (whole word match)
            if f" {term} " in f" {text_lower} " or \
               text_lower.startswith(f"{term} ") or \
               text_lower.endswith(f" {term}"):
                found_terms.append(term)

        return found_terms

    def prioritize_terms(self, terms: List[str], technical_terms: List[str]) -> List[str]:
        """
        Prioritize which terms need definitions most urgently.

        Args:
            terms: All identified financial terms
            technical_terms: Highly technical terms from AI analysis

        Returns:
            Sorted list of terms by priority (highest first)
        """
        # Technical terms get highest priority
        priority_terms = []

        # Add technical terms first
        for term in technical_terms:
            if term.lower() in [t.lower() for t in terms]:
                priority_terms.append(term)

        # Add remaining terms
        for term in terms:
            if term not in priority_terms and term.lower() not in [t.lower() for t in priority_terms]:
                priority_terms.append(term)

        return priority_terms

    def get_extraction_summary(self, extraction_result: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the extraction."""
        terms_count = len(extraction_result.get('terms', []))
        refs_count = len(extraction_result.get('references', []))
        tech_count = len(extraction_result.get('technical_terms', []))
        confidence = extraction_result.get('confidence', 0)

        return f"""Vocabulary Extraction Summary:
- Found {terms_count} financial terms
- Identified {refs_count} specific references
- Detected {tech_count} technical terms requiring definitions
- Confidence: {confidence:.1%}
"""


# Test function
if __name__ == "__main__":
    agent = VocabularyAgent()

    sample_text = """
    I just executed 2 trades for you based on the current market conditions.

    Given the elevated VIX at 22.5 and high volatility in the market, I reduced
    our SPY exposure from 60% to 45% to minimize drawdown risk. The Monte Carlo
    simulation showed a potential 15% drawdown in worst-case scenarios.

    I increased our allocation to TLT (bonds) to 30% for diversification and
    moved 10% to cash to maintain liquidity. The Sharpe ratio improved from
    0.45 to 0.56 with this rebalancing.

    Total slippage was minimal at 0.2%.
    """

    result = agent.extract_financial_terms(sample_text)
    print(json.dumps(result, indent=2))
    print("\n" + agent.get_extraction_summary(result))
