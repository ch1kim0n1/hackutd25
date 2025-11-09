"""
Definition Agent - Fetches and manages financial term definitions.

This agent is responsible for getting clear, concise definitions for financial
terminology using AI or a definitions database.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DefinitionAgent:
    """
    Agent responsible for fetching and caching financial term definitions.
    """

    def __init__(self):
        """Initialize the Definition Agent with AI client and cache."""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.model = "nvidia/llama-3.1-nemotron-70b-instruct"

        # In-memory cache for definitions
        self.definition_cache: Dict[str, Dict[str, Any]] = {}

        # Load pre-defined common definitions
        self._load_common_definitions()

    def _load_common_definitions(self):
        """Load commonly used financial definitions into cache."""
        common_defs = {
            'vix': {
                'term': 'VIX',
                'definition': 'The CBOE Volatility Index, measuring expected stock market volatility over the next 30 days. Often called the "fear gauge."',
                'category': 'index',
                'difficulty': 'intermediate'
            },
            'spy': {
                'term': 'SPY',
                'definition': 'SPDR S&P 500 ETF Trust, an exchange-traded fund that tracks the S&P 500 index.',
                'category': 'instrument',
                'difficulty': 'beginner'
            },
            'sharpe ratio': {
                'term': 'Sharpe Ratio',
                'definition': 'A measure of risk-adjusted return, calculated as (return - risk-free rate) / volatility. Higher is better.',
                'category': 'metric',
                'difficulty': 'advanced'
            },
            'drawdown': {
                'term': 'Drawdown',
                'definition': 'The peak-to-trough decline in portfolio value, expressed as a percentage. Measures worst-case losses.',
                'category': 'risk',
                'difficulty': 'intermediate'
            },
            'monte carlo': {
                'term': 'Monte Carlo Simulation',
                'definition': 'A statistical technique that runs thousands of scenarios with random variables to estimate probable outcomes.',
                'category': 'methodology',
                'difficulty': 'advanced'
            },
            'slippage': {
                'term': 'Slippage',
                'definition': 'The difference between expected trade price and actual execution price, often due to market movement.',
                'category': 'trading',
                'difficulty': 'intermediate'
            },
            'etf': {
                'term': 'ETF',
                'definition': 'Exchange-Traded Fund - a basket of securities that trades on an exchange like a stock.',
                'category': 'instrument',
                'difficulty': 'beginner'
            },
            'allocation': {
                'term': 'Allocation',
                'definition': 'The distribution of investments across different asset classes (stocks, bonds, cash, etc.).',
                'category': 'strategy',
                'difficulty': 'beginner'
            },
            'volatility': {
                'term': 'Volatility',
                'definition': 'The degree of variation in asset prices over time. Higher volatility means larger price swings.',
                'category': 'risk',
                'difficulty': 'beginner'
            },
            'liquidity': {
                'term': 'Liquidity',
                'definition': 'How easily an asset can be bought or sold without affecting its price. Cash is most liquid.',
                'category': 'concept',
                'difficulty': 'beginner'
            },
            'diversification': {
                'term': 'Diversification',
                'definition': 'Spreading investments across different assets to reduce risk ("don\'t put all eggs in one basket").',
                'category': 'strategy',
                'difficulty': 'beginner'
            },
            'rebalancing': {
                'term': 'Rebalancing',
                'definition': 'Adjusting portfolio positions to maintain desired allocation percentages.',
                'category': 'strategy',
                'difficulty': 'intermediate'
            },
            'value at risk': {
                'term': 'Value at Risk (VaR)',
                'definition': 'Maximum expected loss over a given time period at a certain confidence level (e.g., 5% worst case).',
                'category': 'risk',
                'difficulty': 'advanced'
            },
            'var': {
                'term': 'VaR',
                'definition': 'Value at Risk - Maximum expected loss over a given time period at a certain confidence level.',
                'category': 'risk',
                'difficulty': 'advanced'
            },
            'basis point': {
                'term': 'Basis Point',
                'definition': 'One hundredth of a percentage point (0.01%). 100 basis points = 1%.',
                'category': 'unit',
                'difficulty': 'intermediate'
            },
            'yield': {
                'term': 'Yield',
                'definition': 'The income return on an investment, expressed as a percentage of cost or current value.',
                'category': 'metric',
                'difficulty': 'beginner'
            },
            'hedge': {
                'term': 'Hedge',
                'definition': 'An investment that reduces risk in another position (like insurance for your portfolio).',
                'category': 'strategy',
                'difficulty': 'intermediate'
            },
            'beta': {
                'term': 'Beta',
                'definition': 'Measure of volatility relative to the market. Beta > 1 means more volatile than market.',
                'category': 'metric',
                'difficulty': 'advanced'
            },
            'alpha': {
                'term': 'Alpha',
                'definition': 'Excess return compared to a benchmark. Positive alpha means outperformance.',
                'category': 'metric',
                'difficulty': 'advanced'
            }
        }

        for key, definition in common_defs.items():
            self.definition_cache[key.lower()] = definition

    def get_definitions(self, terms: List[str], context: str = "") -> Dict[str, Dict[str, Any]]:
        """
        Get definitions for a list of financial terms.

        Args:
            terms: List of financial terms to define
            context: Original text context (helps provide better definitions)

        Returns:
            Dictionary mapping terms to their definitions
        """
        logger.info(f"📚 Definition Agent: Fetching definitions for {len(terms)} terms...")

        definitions = {}

        for term in terms:
            term_lower = term.lower()

            # Check cache first
            if term_lower in self.definition_cache:
                definitions[term] = self.definition_cache[term_lower]
                logger.info(f"  ✓ '{term}' (cached)")
            else:
                # Fetch from AI
                definition = self._fetch_definition_from_ai(term, context)
                definitions[term] = definition
                # Cache it
                self.definition_cache[term_lower] = definition
                logger.info(f"  ✓ '{term}' (AI-generated)")

        logger.info(f"✅ Definition Agent: Retrieved {len(definitions)} definitions")
        return definitions

    def _fetch_definition_from_ai(self, term: str, context: str = "") -> Dict[str, Any]:
        """Fetch definition from AI model."""
        try:
            prompt = self._create_definition_prompt(term, context)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial education expert. Provide clear, concise definitions for financial terms."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=300
            )

            result = self._parse_definition_response(response.choices[0].message.content, term)
            return result

        except Exception as e:
            logger.error(f"❌ Error fetching definition for '{term}': {e}")
            return {
                'term': term,
                'definition': f"Financial term: {term}",
                'category': 'unknown',
                'difficulty': 'unknown',
                'error': str(e)
            }

    def _create_definition_prompt(self, term: str, context: str = "") -> str:
        """Create prompt for AI to generate definition."""
        base_prompt = f"""Provide a clear, concise definition for the financial term: "{term}"

Requirements:
1. Definition should be 1-2 sentences, easy to understand for beginners
2. Include practical context or example if helpful
3. Categorize as: index, instrument, metric, risk, strategy, concept, trading, methodology, or unit
4. Difficulty level: beginner, intermediate, or advanced

{f'Context where term appears: "{context[:200]}..."' if context else ''}

Return in JSON format:
{{
    "term": "{term}",
    "definition": "Clear, concise definition here",
    "category": "category_here",
    "difficulty": "beginner|intermediate|advanced"
}}
"""
        return base_prompt

    def _parse_definition_response(self, response_text: str, term: str) -> Dict[str, Any]:
        """Parse AI response for definition."""
        try:
            # Extract JSON
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = response_text.strip()

            result = json.loads(json_str)
            return result

        except Exception as e:
            logger.warning(f"Failed to parse definition response: {e}")
            # Fallback - use the raw response as definition
            return {
                'term': term,
                'definition': response_text.strip(),
                'category': 'unknown',
                'difficulty': 'unknown'
            }

    def get_definition_summary(self, definitions: Dict[str, Dict[str, Any]]) -> str:
        """Generate summary of definitions."""
        total = len(definitions)
        categories = {}
        difficulties = {}

        for def_data in definitions.values():
            cat = def_data.get('category', 'unknown')
            diff = def_data.get('difficulty', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
            difficulties[diff] = difficulties.get(diff, 0) + 1

        summary = f"""Definition Summary:
- Total definitions: {total}
- Categories: {', '.join(f'{k}({v})' for k, v in categories.items())}
- Difficulty: {', '.join(f'{k}({v})' for k, v in difficulties.items())}
"""
        return summary

    def clear_cache(self):
        """Clear the definition cache (except common definitions)."""
        # Keep only the pre-loaded common definitions
        self.definition_cache = {k: v for k, v in self.definition_cache.items()
                                  if v.get('preloaded', False)}
        logger.info("Definition cache cleared")


# Test function
if __name__ == "__main__":
    agent = DefinitionAgent()

    test_terms = ['VIX', 'Sharpe ratio', 'drawdown', 'Monte Carlo', 'slippage']

    context = """
    Given the elevated VIX at 22.5, I reduced our SPY exposure.
    The Sharpe ratio improved and Monte Carlo simulation showed reduced drawdown.
    """

    definitions = agent.get_definitions(test_terms, context)

    print(json.dumps(definitions, indent=2))
    print("\n" + agent.get_definition_summary(definitions))
