"""
Output Refinement Pipeline
Orchestrates the post-processing of AI outputs with financial terminology definitions.

This pipeline coordinates three specialized agents:
1. Vocabulary Agent - Extracts financial terms
2. Definition Agent - Fetches/caches definitions
3. Formatting Agent - Creates rich, formatted output

Pipeline flow:
    Raw Text → Vocabulary Agent → Definition Agent → Formatting Agent → Enhanced Output
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from agents.vocabulary_agent import VocabularyAgent
from agents.definition_agent import DefinitionAgent
from agents.formatting_agent import FormattingAgent


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RefinedOutput:
    """Container for refined output in multiple formats."""
    terminal_output: str
    markdown: str
    web_html: str
    web_json: str
    detected_terms: List[str]
    definitions: Dict[str, Dict[str, Any]]
    raw_text: str
    processing_time: float
    stats: Dict[str, Any]


class RefinementPipeline:
    """
    Main orchestrator for the output refinement pipeline.
    
    Coordinates vocabulary extraction, definition fetching, and formatting
    to enhance AI outputs with linked financial terminology.
    """

    def __init__(
        self,
        explanation_level: str = "beginner",
        max_terms: int = 10,
        enable_ai_enhancement: bool = True
    ):
        """
        Initialize the refinement pipeline.

        Args:
            explanation_level: Target audience level ('beginner', 'intermediate', 'advanced')
            max_terms: Maximum number of terms to define per output
            enable_ai_enhancement: Whether to use AI for text restructuring
        """
        logger.info("🔧 Initializing Output Refinement Pipeline...")

        self.explanation_level = explanation_level
        self.max_terms = max_terms
        self.enable_ai_enhancement = enable_ai_enhancement

        # Initialize agents
        try:
            self.vocabulary_agent = VocabularyAgent()
            logger.info("  ✓ Vocabulary Agent initialized")
        except Exception as e:
            logger.error(f"  ✗ Vocabulary Agent failed: {e}")
            raise

        try:
            self.definition_agent = DefinitionAgent()
            logger.info("  ✓ Definition Agent initialized")
        except Exception as e:
            logger.error(f"  ✗ Definition Agent failed: {e}")
            raise

        try:
            self.formatting_agent = FormattingAgent()
            logger.info("  ✓ Formatting Agent initialized")
        except Exception as e:
            logger.error(f"  ✗ Formatting Agent failed: {e}")
            raise

        # Statistics
        self.stats = {
            'total_refinements': 0,
            'total_terms_detected': 0,
            'total_definitions_fetched': 0,
            'cache_hits': 0,
            'errors': 0
        }

        logger.info("✅ Output Refinement Pipeline ready")

    def refine(
        self,
        text: str,
        format: str = "terminal",
        context: Optional[str] = None
    ) -> RefinedOutput:
        """
        Refine the given text by extracting terms, fetching definitions, and formatting.

        Args:
            text: Raw text output from Explainer Agent
            format: Primary output format ('terminal', 'web', 'both')
            context: Additional context for better term extraction

        Returns:
            RefinedOutput containing formatted text in multiple formats
        """
        start_time = datetime.now()

        logger.info("=" * 80)
        logger.info("🎨 Starting Output Refinement Pipeline")
        logger.info("=" * 80)

        try:
            # Step 1: Extract financial terms
            logger.info("\n[1/3] Vocabulary Extraction...")
            vocabulary_result = self.vocabulary_agent.extract_financial_terms(text)

            detected_terms = vocabulary_result.get('terms', [])
            technical_terms = vocabulary_result.get('technical_terms', [])
            references = vocabulary_result.get('references', [])

            logger.info(f"  → Detected {len(detected_terms)} terms")
            logger.info(f"  → Found {len(technical_terms)} technical terms")
            logger.info(f"  → Found {len(references)} references")

            # Prioritize terms
            prioritized_terms = self.vocabulary_agent.prioritize_terms(
                detected_terms,
                technical_terms
            )

            # Limit to max_terms
            selected_terms = prioritized_terms[:self.max_terms]

            if len(prioritized_terms) > self.max_terms:
                logger.info(f"  → Limited to {self.max_terms} most important terms")

            # Step 2: Fetch definitions
            logger.info(f"\n[2/3] Fetching Definitions...")
            definitions = self.definition_agent.get_definitions(
                selected_terms,
                context=context or text
            )

            logger.info(f"  → Retrieved {len(definitions)} definitions")

            # Filter definitions based on explanation level
            filtered_definitions = self._filter_by_level(definitions)
            logger.info(f"  → Filtered to {len(filtered_definitions)} for '{self.explanation_level}' level")

            # Step 3: Format output
            logger.info(f"\n[3/3] Formatting Output...")

            # Generate terminal format
            terminal_result = self.formatting_agent.format_output(
                raw_text=text,
                definitions=filtered_definitions,
                format_type="terminal"
            )

            # Generate markdown format
            markdown_result = self.formatting_agent.format_output(
                raw_text=text,
                definitions=filtered_definitions,
                format_type="markdown"
            )

            # Generate HTML format (for web)
            html_result = self.formatting_agent.format_output(
                raw_text=text,
                definitions=filtered_definitions,
                format_type="html"
            )

            # Generate JSON format (for web API)
            json_result = self.formatting_agent.format_output(
                raw_text=text,
                definitions=filtered_definitions,
                format_type="json"
            )

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Update statistics
            self.stats['total_refinements'] += 1
            self.stats['total_terms_detected'] += len(detected_terms)
            self.stats['total_definitions_fetched'] += len(definitions)

            # Create refined output container
            refined_output = RefinedOutput(
                terminal_output=terminal_result['formatted_text'],
                markdown=markdown_result['formatted_text'],
                web_html=html_result['formatted_text'],
                web_json=json_result['formatted_text'],
                detected_terms=selected_terms,
                definitions=filtered_definitions,
                raw_text=text,
                processing_time=processing_time,
                stats={
                    'total_terms': len(detected_terms),
                    'selected_terms': len(selected_terms),
                    'definitions_provided': len(filtered_definitions),
                    'processing_time_ms': int(processing_time * 1000)
                }
            )

            logger.info(f"\n✅ Refinement complete in {processing_time:.2f}s")
            logger.info(f"   Terms: {len(detected_terms)} detected → {len(selected_terms)} selected → {len(filtered_definitions)} defined")
            logger.info("=" * 80)

            return refined_output

        except Exception as e:
            logger.error(f"❌ Refinement pipeline error: {e}", exc_info=True)
            self.stats['errors'] += 1

            # Return minimal output on error
            return RefinedOutput(
                terminal_output=text,
                markdown=text,
                web_html=f"<div>{text}</div>",
                web_json='{"text": "' + text.replace('"', '\\"') + '"}',
                detected_terms=[],
                definitions={},
                raw_text=text,
                processing_time=0.0,
                stats={'error': str(e)}
            )

    def _filter_by_level(
        self,
        definitions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Filter definitions based on user's explanation level.

        For beginners: Include beginner + intermediate terms
        For intermediate: Include all terms
        For advanced: Include all terms (user likely knows basics)
        """
        if self.explanation_level == "beginner":
            # Focus on beginner and intermediate terms
            return {
                term: def_data
                for term, def_data in definitions.items()
                if def_data.get('difficulty') in ['beginner', 'intermediate', 'unknown']
            }
        elif self.explanation_level == "intermediate":
            # Include all terms
            return definitions
        else:  # advanced
            # Include all terms but prioritize advanced ones
            return definitions

    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        return {
            **self.stats,
            'explanation_level': self.explanation_level,
            'max_terms_per_output': self.max_terms,
            'glossary_terms': len(self.definition_agent.definition_cache),
            'ai_enhancement_enabled': self.enable_ai_enhancement
        }

    def update_config(
        self,
        explanation_level: Optional[str] = None,
        max_terms: Optional[int] = None,
        enable_ai_enhancement: Optional[bool] = None
    ):
        """Update pipeline configuration."""
        if explanation_level:
            self.explanation_level = explanation_level
            logger.info(f"Updated explanation level: {explanation_level}")

        if max_terms:
            self.max_terms = max_terms
            logger.info(f"Updated max terms: {max_terms}")

        if enable_ai_enhancement is not None:
            self.enable_ai_enhancement = enable_ai_enhancement
            logger.info(f"Updated AI enhancement: {enable_ai_enhancement}")

    def clear_cache(self):
        """Clear the definition cache."""
        self.definition_agent.definition_cache.clear()
        logger.info("Definition cache cleared")


# Standalone test/demo function
def demo_pipeline():
    """Demonstrate the refinement pipeline with sample text."""
    print("\n" + "=" * 80)
    print("Output Refinement Pipeline - Demo")
    print("=" * 80 + "\n")

    # Sample financial explanation text
    sample_text = """
I just executed 2 strategic rebalancing trades to optimize your portfolio.

Market Analysis:
The VIX has elevated to 22.5, indicating increased volatility in the market.
Our risk models detected heightened correlation between equity positions,
which could amplify drawdown during market stress.

Actions Taken:
1. Reduced SPY allocation from 60% to 45% (-15%)
2. Increased TLT (Treasury bonds) from 20% to 30% (+10%)
3. Raised cash position to 10% for improved liquidity

Risk Impact:
The Monte Carlo simulation with 10,000 scenarios shows:
- Reduced worst-case drawdown from 28% to 18%
- Improved Sharpe ratio from 0.45 to 0.56
- Maintained diversification across asset classes

Execution Quality:
Total slippage was only 0.2%, well within acceptable limits. I used VWAP
execution to minimize market impact. All trades settled successfully.

Your portfolio now has better downside protection while maintaining upside
potential. The current allocation aligns with your moderate risk tolerance.
    """

    # Create pipeline
    pipeline = RefinementPipeline(
        explanation_level="beginner",
        max_terms=8
    )

    # Refine the output
    refined = pipeline.refine(sample_text, format="terminal")

    # Display results
    print("\n📊 TERMINAL OUTPUT:")
    print(refined.terminal_output)

    print("\n" + "=" * 80)
    print(f"Processing Time: {refined.processing_time:.2f}s")
    print(f"Terms Detected: {len(refined.detected_terms)}")
    print(f"Definitions Provided: {len(refined.definitions)}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    demo_pipeline()
