"""
Formatting Agent - Enhances text output with linked definitions and rich formatting.

This agent takes raw text + definitions and creates a beautifully formatted
output with hover-able terms (for terminal) and clean presentation.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from openai import OpenAI
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FormattingAgent:
    """
    Agent responsible for formatting output with linked definitions and enhanced presentation.
    """

    def __init__(self):
        """Initialize the Formatting Agent with AI client."""
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.model = "nvidia/llama-3.1-nemotron-70b-instruct"

        # ANSI color codes for terminal
        self.colors = {
            'reset': '\033[0m',
            'bold': '\033[1m',
            'dim': '\033[2m',
            'italic': '\033[3m',
            'underline': '\033[4m',
            'blue': '\033[94m',
            'cyan': '\033[96m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'red': '\033[91m',
            'magenta': '\033[95m',
            'white': '\033[97m',
            'gray': '\033[90m'
        }

    def format_output(
        self,
        raw_text: str,
        definitions: Dict[str, Dict[str, Any]],
        format_type: str = "terminal"
    ) -> Dict[str, Any]:
        """
        Format the output with linked definitions and enhanced presentation.

        Args:
            raw_text: The raw text output from Explainer Agent
            definitions: Dictionary of term definitions
            format_type: Output format ('terminal', 'html', 'markdown', 'json')

        Returns:
            Formatted output in requested format
        """
        logger.info(f"🎨 Formatting Agent: Enhancing output ({format_type} format)...")

        try:
            # First, ask AI to restructure and improve the text
            enhanced_text = self._enhance_text_with_ai(raw_text, definitions)

            # Then format based on type
            if format_type == "terminal":
                formatted = self._format_for_terminal(enhanced_text, definitions)
            elif format_type == "markdown":
                formatted = self._format_for_markdown(enhanced_text, definitions)
            elif format_type == "html":
                formatted = self._format_for_html(enhanced_text, definitions)
            elif format_type == "json":
                formatted = self._format_for_json(enhanced_text, definitions)
            else:
                formatted = enhanced_text

            logger.info("✅ Formatting Agent: Output enhanced successfully")

            return {
                'formatted_text': formatted,
                'format_type': format_type,
                'terms_linked': len(definitions),
                'raw_text': raw_text,
                'enhanced_text': enhanced_text,
                'definitions': definitions
            }

        except Exception as e:
            logger.error(f"❌ Formatting Agent error: {e}")
            return {
                'formatted_text': raw_text,
                'format_type': 'plain',
                'terms_linked': 0,
                'error': str(e)
            }

    def _enhance_text_with_ai(self, text: str, definitions: Dict[str, Dict[str, Any]]) -> str:
        """Use AI to restructure and improve the text presentation."""
        logger.info("  → AI is restructuring text for better presentation...")

        try:
            prompt = self._create_formatting_prompt(text, definitions)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at presenting financial information clearly and professionally."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=2000
            )

            enhanced = response.choices[0].message.content.strip()
            logger.info("  ✓ Text restructured by AI")
            return enhanced

        except Exception as e:
            logger.warning(f"  ⚠ AI enhancement failed: {e}, using original text")
            return text

    def _create_formatting_prompt(self, text: str, definitions: Dict[str, Dict[str, Any]]) -> str:
        """Create prompt for AI to enhance text formatting."""
        terms_list = list(definitions.keys())

        return f"""Rewrite the following financial explanation to make it more presentable and user-friendly.

Requirements:
1. Keep the same information but improve structure and clarity
2. Use clear sections with headers (e.g., "Summary:", "Actions Taken:", "Impact:")
3. Use bullet points or numbered lists where appropriate
4. Keep technical terms ({', '.join(terms_list[:5])}...) as-is - they will be linked to definitions
5. Make it professional but approachable
6. Keep it concise - don't add unnecessary length

Original text:
\"\"\"
{text}
\"\"\"

Return ONLY the improved text, no explanations or meta-commentary.
"""

    def _format_for_terminal(self, text: str, definitions: Dict[str, Dict[str, Any]]) -> str:
        """
        Format for rich terminal display with color and 'hover' definitions.

        Creates a format where terms are highlighted and definitions appear below.
        """
        # Create header
        c = self.colors
        output = []

        # Title
        output.append(f"\n{c['bold']}{c['cyan']}{'═' * 80}{c['reset']}")
        output.append(f"{c['bold']}{c['cyan']}  APEX AI FINANCIAL EXPLANATION{c['reset']}")
        output.append(f"{c['bold']}{c['cyan']}{'═' * 80}{c['reset']}\n")

        # Process text to highlight defined terms
        highlighted_text = text
        terms_found = []

        for term, def_data in definitions.items():
            # Create pattern for case-insensitive match (whole word)
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)

            # Find all occurrences
            matches = pattern.finditer(highlighted_text)

            for match in matches:
                # Only highlight first occurrence of each term
                if term.lower() not in [t.lower() for t in terms_found]:
                    original = match.group()
                    # Highlight with color and markers
                    highlighted = f"{c['yellow']}{c['bold']}{original}{c['reset']}{c['blue']}*{c['reset']}"
                    highlighted_text = highlighted_text.replace(original, highlighted, 1)
                    terms_found.append(term)

        # Add the highlighted text
        output.append(highlighted_text)

        # Add definitions glossary at the bottom
        if definitions:
            output.append(f"\n{c['bold']}{c['cyan']}{'─' * 80}{c['reset']}")
            output.append(f"{c['bold']}{c['cyan']}  GLOSSARY (Terms marked with *){c['reset']}")
            output.append(f"{c['bold']}{c['cyan']}{'─' * 80}{c['reset']}\n")

            # Sort by difficulty for better reading experience
            sorted_defs = sorted(
                definitions.items(),
                key=lambda x: {'beginner': 0, 'intermediate': 1, 'advanced': 2, 'unknown': 3}
                .get(x[1].get('difficulty', 'unknown'), 3)
            )

            for term, def_data in sorted_defs:
                if term.lower() in [t.lower() for t in terms_found]:
                    difficulty = def_data.get('difficulty', 'unknown')
                    category = def_data.get('category', 'unknown')

                    # Color code by difficulty
                    if difficulty == 'beginner':
                        color = c['green']
                    elif difficulty == 'intermediate':
                        color = c['yellow']
                    else:
                        color = c['red']

                    output.append(f"{c['bold']}{color}• {def_data.get('term', term)}{c['reset']} "
                                  f"{c['gray']}[{category}]{c['reset']}")
                    output.append(f"  {def_data.get('definition', 'No definition available')}\n")

        # Footer
        output.append(f"{c['bold']}{c['cyan']}{'═' * 80}{c['reset']}\n")

        return '\n'.join(output)

    def _format_for_markdown(self, text: str, definitions: Dict[str, Dict[str, Any]]) -> str:
        """Format for markdown with linked definitions."""
        output = []

        output.append("# 📊 APEX AI Financial Explanation\n")
        output.append("---\n")

        # Process text to link terms
        linked_text = text
        terms_found = []

        for term, def_data in definitions.items():
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(linked_text)

            for match in matches:
                if term.lower() not in [t.lower() for t in terms_found]:
                    original = match.group()
                    # Create markdown link to glossary
                    linked = f"**{original}***"
                    linked_text = linked_text.replace(original, linked, 1)
                    terms_found.append(term)

        output.append(linked_text)
        output.append("\n---\n")

        # Add glossary
        if definitions:
            output.append("## 📚 Glossary\n")

            sorted_defs = sorted(
                definitions.items(),
                key=lambda x: x[0].lower()
            )

            for term, def_data in sorted_defs:
                if term.lower() in [t.lower() for t in terms_found]:
                    difficulty_emoji = {
                        'beginner': '🟢',
                        'intermediate': '🟡',
                        'advanced': '🔴',
                        'unknown': '⚪'
                    }.get(def_data.get('difficulty', 'unknown'), '⚪')

                    output.append(f"**{def_data.get('term', term)}** {difficulty_emoji} "
                                  f"*({def_data.get('category', 'unknown')})*")
                    output.append(f"> {def_data.get('definition', 'No definition available')}\n")

        return '\n'.join(output)

    def _format_for_html(self, text: str, definitions: Dict[str, Dict[str, Any]]) -> str:
        """Format for HTML with hover tooltips."""
        output = []

        output.append('<div class="apex-explanation">')
        output.append('<h1>📊 APEX AI Financial Explanation</h1>')
        output.append('<hr>')

        # Process text to add hover tooltips
        html_text = text
        terms_found = []

        for term, def_data in definitions.items():
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(html_text)

            for match in matches:
                if term.lower() not in [t.lower() for t in terms_found]:
                    original = match.group()
                    definition = def_data.get('definition', 'No definition')
                    # Create span with tooltip
                    tooltip = f'<span class="financial-term" title="{definition}">{original}</span>'
                    html_text = html_text.replace(original, tooltip, 1)
                    terms_found.append(term)

        output.append(f'<div class="explanation-text">{html_text}</div>')
        output.append('<hr>')

        # Add glossary
        if definitions:
            output.append('<h2>📚 Glossary</h2>')
            output.append('<dl class="glossary">')

            for term, def_data in sorted(definitions.items(), key=lambda x: x[0].lower()):
                if term.lower() in [t.lower() for t in terms_found]:
                    output.append(f'<dt>{def_data.get("term", term)}</dt>')
                    output.append(f'<dd>{def_data.get("definition", "No definition")}</dd>')

            output.append('</dl>')

        output.append('</div>')

        return '\n'.join(output)

    def _format_for_json(self, text: str, definitions: Dict[str, Dict[str, Any]]) -> str:
        """Format as structured JSON."""
        result = {
            'text': text,
            'sections': self._extract_sections(text),
            'terms': [],
            'definitions': definitions
        }

        # Find term positions in text
        for term, def_data in definitions.items():
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(text)

            for match in matches:
                result['terms'].append({
                    'term': match.group(),
                    'position': match.start(),
                    'definition': def_data
                })

        return json.dumps(result, indent=2)

    def _extract_sections(self, text: str) -> List[Dict[str, str]]:
        """Extract sections from text based on headers."""
        sections = []
        lines = text.split('\n')

        current_section = {'title': 'Introduction', 'content': ''}

        for line in lines:
            # Check if line is a header (ends with : or starts with ##)
            if line.strip().endswith(':') and len(line.strip()) < 50:
                if current_section['content'].strip():
                    sections.append(current_section)
                current_section = {'title': line.strip()[:-1], 'content': ''}
            elif line.strip().startswith('##'):
                if current_section['content'].strip():
                    sections.append(current_section)
                current_section = {'title': line.strip()[2:].strip(), 'content': ''}
            else:
                current_section['content'] += line + '\n'

        # Add last section
        if current_section['content'].strip():
            sections.append(current_section)

        return sections


# Test function
if __name__ == "__main__":
    agent = FormattingAgent()

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

    sample_definitions = {
        'VIX': {
            'term': 'VIX',
            'definition': 'The CBOE Volatility Index, measuring expected market volatility. Often called the "fear gauge."',
            'category': 'index',
            'difficulty': 'intermediate'
        },
        'SPY': {
            'term': 'SPY',
            'definition': 'SPDR S&P 500 ETF Trust, tracking the S&P 500 index.',
            'category': 'instrument',
            'difficulty': 'beginner'
        },
        'drawdown': {
            'term': 'Drawdown',
            'definition': 'Peak-to-trough decline in portfolio value.',
            'category': 'risk',
            'difficulty': 'intermediate'
        },
        'Monte Carlo': {
            'term': 'Monte Carlo Simulation',
            'definition': 'Statistical technique running thousands of scenarios to estimate outcomes.',
            'category': 'methodology',
            'difficulty': 'advanced'
        },
        'Sharpe ratio': {
            'term': 'Sharpe Ratio',
            'definition': 'Measure of risk-adjusted return. Higher is better.',
            'category': 'metric',
            'difficulty': 'advanced'
        }
    }

    result = agent.format_output(sample_text, sample_definitions, format_type="terminal")
    print(result['formatted_text'])
