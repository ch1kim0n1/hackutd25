# backend/services/voice_goal_parser.py
"""
Voice command parser for goal creation.
Extracts goal parameters from natural language voice input.
"""
import re
from typing import Dict, Optional, Tuple
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import dateutil.parser as date_parser


class VoiceGoalParser:
    """
    Parse natural language goal commands into structured goal data.

    Examples:
    - "I want $1 million in 10 years"
    - "Save $50,000 for a house down payment by 2028"
    - "Retire with $2M in 20 years"
    - "I need $100k for college in 5 years"
    """

    def __init__(self):
        """Initialize parser"""
        # Goal type patterns
        self.goal_patterns = {
            'retirement': ['retire', 'retirement'],
            'house': ['house', 'home', 'down payment', 'mortgage'],
            'education': ['college', 'university', 'education', 'tuition'],
            'vacation': ['vacation', 'trip', 'travel'],
            'car': ['car', 'vehicle', 'auto'],
            'emergency': ['emergency fund', 'rainy day'],
        }

    def parse(self, text: str) -> Dict:
        """
        Parse voice input into goal parameters.

        Args:
            text: Natural language goal description

        Returns:
            Dict with extracted parameters
        """
        text_lower = text.lower()

        # Extract parameters
        target_amount = self._extract_amount(text_lower)
        years, target_date = self._extract_timeline(text_lower)
        goal_type = self._extract_goal_type(text_lower)
        monthly_contribution = self._extract_monthly_contribution(text_lower)
        risk_tolerance = self._extract_risk_tolerance(text_lower)

        # Generate goal name
        goal_name = self._generate_goal_name(target_amount, years, goal_type)

        return {
            "name": goal_name,
            "goal_type": goal_type,
            "target_amount": target_amount,
            "target_date": target_date,
            "years_to_goal": years,
            "monthly_contribution": monthly_contribution,
            "risk_tolerance": risk_tolerance,
            "voice_input_text": text,
            "parsed_successfully": target_amount is not None and years is not None
        }

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract dollar amount from text"""
        # Pattern 1: $X million/M/k/thousand
        patterns = [
            r'\$?\s*(\d+(?:\.\d+)?)\s*million',
            r'\$?\s*(\d+(?:\.\d+)?)\s*M\b',
            r'\$?\s*(\d+(?:\.\d+)?)\s*k\b',
            r'\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = float(match.group(1).replace(',', ''))

                # Apply multiplier
                if 'million' in text.lower() or ' M' in text or ' m' in text:
                    amount *= 1_000_000
                elif ' k' in text.lower():
                    amount *= 1_000

                return amount

        return None

    def _extract_timeline(self, text: str) -> Tuple[Optional[int], Optional[str]]:
        """Extract timeline (years or target date)"""
        # Pattern 1: "in X years"
        match = re.search(r'in\s+(\d+)\s+years?', text)
        if match:
            years = int(match.group(1))
            target_date = (date.today() + relativedelta(years=years)).isoformat()
            return years, target_date

        # Pattern 2: "by YYYY" or "by Month Year"
        match = re.search(r'by\s+(\d{4})', text)
        if match:
            year = int(match.group(1))
            target_date = date(year, 12, 31).isoformat()
            years = year - date.today().year
            return years, target_date

        # Pattern 3: "by [Month] [Year]"
        match = re.search(r'by\s+([a-z]+)\s+(\d{4})', text, re.IGNORECASE)
        if match:
            try:
                parsed_date = date_parser.parse(f"{match.group(1)} {match.group(2)}")
                target_date = parsed_date.date().isoformat()
                years = (parsed_date.date() - date.today()).days // 365
                return years, target_date
            except:
                pass

        return None, None

    def _extract_goal_type(self, text: str) -> str:
        """Extract goal type from keywords"""
        for goal_type, keywords in self.goal_patterns.items():
            if any(keyword in text for keyword in keywords):
                return goal_type

        return 'general'

    def _extract_monthly_contribution(self, text: str) -> float:
        """Extract monthly contribution amount if mentioned"""
        # Pattern: "save/contribute $X per month/monthly"
        patterns = [
            r'(?:save|contribute|invest)\s+\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s+(?:per month|monthly|each month)',
            r'\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s+(?:per month|monthly|a month)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))

        return 0.0

    def _extract_risk_tolerance(self, text: str) -> str:
        """Extract risk tolerance if mentioned"""
        if any(word in text for word in ['aggressive', 'high risk', 'growth']):
            return 'aggressive'
        elif any(word in text for word in ['conservative', 'safe', 'low risk']):
            return 'conservative'
        else:
            return 'moderate'

    def _generate_goal_name(
        self,
        amount: Optional[float],
        years: Optional[int],
        goal_type: str
    ) -> str:
        """Generate a descriptive goal name"""
        if amount and years:
            if goal_type == 'retirement':
                return f"Retire with ${self._format_amount(amount)} in {years} years"
            elif goal_type == 'house':
                return f"Save ${self._format_amount(amount)} for house down payment"
            elif goal_type == 'education':
                return f"Save ${self._format_amount(amount)} for education"
            else:
                return f"Reach ${self._format_amount(amount)} in {years} years"

        return "Financial Goal"

    def _format_amount(self, amount: float) -> str:
        """Format amount for display"""
        if amount >= 1_000_000:
            return f"{amount / 1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"{amount / 1_000:.0f}K"
        else:
            return f"{amount:.0f}"

    def validate_goal(self, parsed_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate parsed goal data.

        Args:
            parsed_data: Parsed goal dict

        Returns:
            (is_valid, error_message)
        """
        # Check required fields
        if not parsed_data.get('target_amount'):
            return False, "Could not extract target amount from voice input"

        if not parsed_data.get('years_to_goal'):
            return False, "Could not extract timeline from voice input"

        # Check reasonable values
        if parsed_data['target_amount'] < 100:
            return False, "Target amount seems too low (minimum $100)"

        if parsed_data['target_amount'] > 1_000_000_000:
            return False, "Target amount exceeds $1 billion"

        if parsed_data['years_to_goal'] < 1:
            return False, "Timeline must be at least 1 year"

        if parsed_data['years_to_goal'] > 100:
            return False, "Timeline cannot exceed 100 years"

        return True, None

    def extract_all_goals(self, text: str) -> List[Dict]:
        """
        Extract multiple goals from text if present.

        Args:
            text: Voice input text

        Returns:
            List of parsed goal dicts
        """
        # Split on common separators
        sentences = re.split(r'\.\s+(?:and\s+)?|,\s+(?:and\s+)?', text)

        goals = []
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['want', 'need', 'save', 'retire', 'goal']):
                parsed = self.parse(sentence)
                if parsed.get('parsed_successfully'):
                    goals.append(parsed)

        return goals if goals else [self.parse(text)]


# Global instance
voice_parser = VoiceGoalParser()
