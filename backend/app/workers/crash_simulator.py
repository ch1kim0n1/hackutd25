from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import numpy as np


@dataclass
class CrashScenario:
	symbol: str = "SPY"
	start_price: float = 450.0
	days: int = 60
	mu_annual: float = 0.07          # annual drift
	sigma_annual: float = 0.18       # annual volatility
	crash_day: int = 10              # day index to crash (0-based)
	crash_severity: float = 0.25     # 25% instantaneous drop
	recovery_speed: float = 0.05     # additive daily drift boost during recovery
	recovery_days: int = 20          # days with boosted drift after crash
	seed: Optional[int] = 42


def simulate_crash(scenario: CrashScenario) -> Dict[str, List[Dict]]:
	"""
	Simulate a geometric Brownian motion price path with a discrete crash shock
	and a recovery drift boost.
	Returns a dict with 'symbol' and 'series' of {t, price}.
	"""
	if scenario.seed is not None:
		np.random.seed(scenario.seed)

	dt = 1.0 / 252.0  # daily step in trading year
	mu_dt = scenario.mu_annual * dt
	sigma_dt = scenario.sigma_annual * math.sqrt(dt)

	prices = [scenario.start_price]
	now = datetime.utcnow()
	timestamps = [now]

	for day in range(1, scenario.days + 1):
		price_prev = prices[-1]

		# Shock on crash day
		if day == scenario.crash_day:
			price_prev *= (1.0 - scenario.crash_severity)

		# Drift boost during recovery window after crash
		drift = mu_dt
		if scenario.crash_day < day <= scenario.crash_day + scenario.recovery_days:
			drift += scenario.recovery_speed * dt

		# Geometric Brownian Motion
		noise = np.random.normal(0.0, 1.0)
		price_new = price_prev * math.exp((drift - 0.5 * sigma_dt * sigma_dt) + sigma_dt * noise)
		prices.append(float(price_new))
		timestamps.append(now + timedelta(days=day))

	series = [
		{
			"t": t.isoformat() + "Z",
			"price": p
		}
		for t, p in zip(timestamps, prices)
	]

	return {
		"symbol": scenario.symbol,
		"series": series
	}


