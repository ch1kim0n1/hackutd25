# backend/services/subscription_detector.py
"""
ML-based subscription detection service for APEX.
Identifies recurring transactions and potential waste.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal
from collections import defaultdict
import re


class SubscriptionDetector:
    """
    ML-based recurring transaction detector.
    Uses pattern matching and heuristics to identify subscriptions.
    """

    # Known subscription merchants
    KNOWN_SUBSCRIPTIONS = {
        "netflix": {"category": "streaming", "typical_amount": 15.49},
        "spotify": {"category": "streaming", "typical_amount": 10.99},
        "amazon prime": {"category": "shopping", "typical_amount": 14.99},
        "hulu": {"category": "streaming", "typical_amount": 7.99},
        "disney": {"category": "streaming", "typical_amount": 7.99},
        "apple music": {"category": "streaming", "typical_amount": 10.99},
        "youtube premium": {"category": "streaming", "typical_amount": 11.99},
        "dropbox": {"category": "software", "typical_amount": 11.99},
        "adobe": {"category": "software", "typical_amount": 54.99},
        "microsoft 365": {"category": "software", "typical_amount": 6.99},
        "icloud": {"category": "storage", "typical_amount": 0.99},
        "google one": {"category": "storage", "typical_amount": 1.99},
        "planet fitness": {"category": "gym", "typical_amount": 10.00},
        "la fitness": {"category": "gym", "typical_amount": 29.99},
        "nyt": {"category": "news", "typical_amount": 17.00},
        "wsj": {"category": "news", "typical_amount": 38.99},
    }

    def __init__(self):
        """Initialize detector"""
        pass

    def detect_recurring_patterns(
        self,
        transactions: List[Dict]
    ) -> List[Dict]:
        """
        Detect recurring transaction patterns.

        Args:
            transactions: List of transaction dicts with date, amount, name, merchant

        Returns:
            List of detected subscriptions with confidence scores
        """
        # Group transactions by merchant/name
        merchant_groups = defaultdict(list)

        for txn in transactions:
            merchant_key = self._normalize_merchant_name(
                txn.get('merchant_name') or txn.get('name', '')
            )
            merchant_groups[merchant_key].append(txn)

        # Detect recurring patterns
        subscriptions = []

        for merchant_key, txns in merchant_groups.items():
            # Need at least 2 transactions to detect pattern
            if len(txns) < 2:
                continue

            # Sort by date
            txns_sorted = sorted(txns, key=lambda x: x['date'])

            # Check if amounts are consistent
            amounts = [Decimal(str(t['amount'])) for t in txns_sorted]
            avg_amount = sum(amounts) / len(amounts)
            amount_variance = sum(abs(a - avg_amount) for a in amounts) / len(amounts)

            # Low variance = likely subscription
            if amount_variance < avg_amount * 0.1:  # 10% variance tolerance
                # Check time intervals between transactions
                dates = [datetime.fromisoformat(t['date']) if isinstance(t['date'], str) else t['date'] for t in txns_sorted]
                intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]

                if intervals:
                    avg_interval = sum(intervals) / len(intervals)

                    # Determine billing cycle
                    billing_cycle = self._classify_interval(avg_interval)

                    if billing_cycle:
                        # Calculate confidence
                        confidence = self._calculate_confidence(
                            merchant_key, amounts, intervals, len(txns)
                        )

                        # Check if it's a known subscription
                        category = self._categorize_subscription(merchant_key)

                        subscriptions.append({
                            "merchant": merchant_key,
                            "original_name": txns_sorted[0].get('merchant_name') or txns_sorted[0].get('name'),
                            "amount": float(avg_amount),
                            "billing_cycle": billing_cycle,
                            "category": category,
                            "detection_confidence": confidence,
                            "transaction_count": len(txns),
                            "first_detected": txns_sorted[0]['date'],
                            "last_transaction": txns_sorted[-1]['date'],
                            "is_known_subscription": merchant_key in self.KNOWN_SUBSCRIPTIONS,
                        })

        return subscriptions

    def identify_waste(
        self,
        subscriptions: List[Dict],
        usage_data: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Identify potentially wasteful subscriptions.

        Args:
            subscriptions: List of detected subscriptions
            usage_data: Optional dict mapping subscription to usage frequency

        Returns:
            List of subscriptions flagged as potential waste
        """
        waste_subscriptions = []

        for sub in subscriptions:
            waste_score = 0
            reasons = []

            # Check for duplicates (e.g., multiple streaming services)
            category = sub.get('category')
            if category in ['streaming', 'storage']:
                similar_count = sum(1 for s in subscriptions if s.get('category') == category)
                if similar_count > 2:
                    waste_score += 30
                    reasons.append(f"You have {similar_count} {category} subscriptions")

            # Check amount vs typical (overpaying?)
            merchant = sub['merchant']
            if merchant in self.KNOWN_SUBSCRIPTIONS:
                typical = self.KNOWN_SUBSCRIPTIONS[merchant]['typical_amount']
                if sub['amount'] > typical * 1.2:  # 20% more than typical
                    waste_score += 20
                    reasons.append(f"Paying ${sub['amount']:.2f} vs typical ${typical:.2f}")

            # Check usage (if data available)
            if usage_data and merchant in usage_data:
                usage = usage_data[merchant]
                if usage == 'never':
                    waste_score += 50
                    reasons.append("Never used")
                elif usage == 'rarely':
                    waste_score += 30
                    reasons.append("Rarely used")

            # High cost subscriptions deserve scrutiny
            if sub['amount'] > 50:
                waste_score += 10
                reasons.append(f"High cost (${sub['amount']:.2f}/month)")

            # Annual cost
            annual_cost = self._calculate_annual_cost(sub['amount'], sub['billing_cycle'])

            if waste_score > 20:  # Threshold for flagging
                waste_subscriptions.append({
                    **sub,
                    "waste_score": waste_score,
                    "waste_reasons": reasons,
                    "annual_cost": annual_cost,
                    "potential_savings": annual_cost
                })

        return sorted(waste_subscriptions, key=lambda x: x['waste_score'], reverse=True)

    def suggest_alternatives(
        self,
        subscription: Dict
    ) -> Optional[Dict]:
        """
        Suggest cheaper alternatives.

        Args:
            subscription: Subscription dict

        Returns:
            Alternative recommendation or None
        """
        merchant = subscription['merchant']
        category = subscription.get('category')

        alternatives = {
            'streaming': {
                'name': 'Ad-supported tier',
                'savings': subscription['amount'] * 0.4,  # ~40% savings
                'description': 'Consider switching to ad-supported plans on Netflix, Hulu, etc.'
            },
            'storage': {
                'name': 'Annual plan',
                'savings': subscription['amount'] * 2,  # 2 months free
                'description': 'Annual plans often save 2 months of cost'
            },
            'gym': {
                'name': 'Home workout apps',
                'savings': subscription['amount'] - 10,
                'description': 'Apps like Peloton Digital ($12.99) or Apple Fitness+ ($9.99)'
            },
        }

        if category in alternatives:
            alt = alternatives[category]
            annual_savings = alt['savings'] * 12 if subscription['billing_cycle'] == 'monthly' else alt['savings']
            return {
                'alternative_name': alt['name'],
                'description': alt['description'],
                'monthly_savings': alt['savings'],
                'annual_savings': annual_savings
            }

        return None

    def _normalize_merchant_name(self, name: str) -> str:
        """Normalize merchant name for grouping"""
        # Lowercase and remove special chars
        name = name.lower()
        name = re.sub(r'[^a-z0-9\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()

        # Check for known patterns
        for known in self.KNOWN_SUBSCRIPTIONS.keys():
            if known in name:
                return known

        return name

    def _classify_interval(self, days: float) -> Optional[str]:
        """Classify billing interval"""
        if 27 <= days <= 33:  # ~30 days
            return "monthly"
        elif 85 <= days <= 95:  # ~90 days
            return "quarterly"
        elif 350 <= days <= 370:  # ~365 days
            return "annual"
        elif 13 <= days <= 15:  # ~14 days
            return "biweekly"
        elif 6 <= days <= 8:  # ~7 days
            return "weekly"
        return None

    def _calculate_confidence(
        self,
        merchant: str,
        amounts: List[Decimal],
        intervals: List[int],
        count: int
    ) -> float:
        """Calculate confidence score (0-1)"""
        confidence = 0.5  # Base confidence

        # More transactions = higher confidence
        if count >= 6:
            confidence += 0.2
        elif count >= 3:
            confidence += 0.1

        # Consistent amounts
        avg_amount = sum(amounts) / len(amounts)
        variance = sum(abs(a - avg_amount) for a in amounts) / len(amounts)
        if variance < avg_amount * 0.05:  # 5% variance
            confidence += 0.15

        # Consistent intervals
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            interval_variance = sum(abs(i - avg_interval) for i in intervals) / len(intervals)
            if interval_variance < 3:  # Within 3 days
                confidence += 0.15

        # Known subscription
        if merchant in self.KNOWN_SUBSCRIPTIONS:
            confidence += 0.1

        return min(confidence, 1.0)

    def _categorize_subscription(self, merchant: str) -> str:
        """Categorize subscription"""
        if merchant in self.KNOWN_SUBSCRIPTIONS:
            return self.KNOWN_SUBSCRIPTIONS[merchant]['category']

        # Heuristics
        if any(word in merchant for word in ['stream', 'video', 'music', 'tv']):
            return 'streaming'
        elif any(word in merchant for word in ['cloud', 'storage', 'drive']):
            return 'storage'
        elif any(word in merchant for word in ['gym', 'fitness', 'yoga']):
            return 'gym'
        elif any(word in merchant for word in ['software', 'app', 'saas']):
            return 'software'
        elif any(word in merchant for word in ['news', 'magazine', 'times']):
            return 'news'

        return 'other'

    def _calculate_annual_cost(self, amount: float, billing_cycle: str) -> float:
        """Calculate annual cost based on billing cycle"""
        multipliers = {
            'weekly': 52,
            'biweekly': 26,
            'monthly': 12,
            'quarterly': 4,
            'annual': 1
        }
        return amount * multipliers.get(billing_cycle, 12)


# Global instance
subscription_detector = SubscriptionDetector()
