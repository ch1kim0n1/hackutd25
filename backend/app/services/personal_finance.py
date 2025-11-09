from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .db import db


class PersonalFinanceService:
	"""
	Personal finance management backed by MongoDB (motor).
	Collections:
	- finance_accounts
	- finance_transactions
	- finance_budgets
	"""

	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.accounts = db["finance_accounts"]
		self.transactions = db["finance_transactions"]
		self.budgets = db["finance_budgets"]

	async def ensure_indexes(self) -> None:
		await self.accounts.create_index("user_id")
		await self.transactions.create_index([("user_id", 1), ("date", -1)])
		await self.transactions.create_index([("user_id", 1), ("account_id", 1), ("date", -1)])
		await self.transactions.create_index([("user_id", 1), ("category", 1), ("date", -1)])
		await self.budgets.create_index([("user_id", 1), ("month", 1)], unique=True)

	# Accounts
	async def add_account(self, user_id: str, name: str, type: str, institution: Optional[str] = None, balance: float = 0.0) -> Dict[str, Any]:
		doc = {
			"user_id": user_id,
			"name": name,
			"type": type,
			"institution": institution,
			"balance": balance,
			"created_at": datetime.utcnow()
		}
		res = await self.accounts.insert_one(doc)
		doc["_id"] = str(res.inserted_id)
		return doc

	async def list_accounts(self, user_id: str) -> List[Dict[str, Any]]:
		cursor = self.accounts.find({"user_id": user_id})
		results: List[Dict[str, Any]] = []
		async for doc in cursor:
			doc["_id"] = str(doc["_id"])
			results.append(doc)
		return results

	# Transactions
	async def import_transactions(self, user_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
		"""
		Bulk import transactions for a user. Items fields:
		- account_id, date (ISO), amount, merchant, category, notes, pending
		"""
		prepared = []
		for it in items:
			prepared.append({
				"user_id": user_id,
				"account_id": it.get("account_id"),
				"date": datetime.fromisoformat(it["date"].replace("Z", "+00:00")) if isinstance(it.get("date"), str) else it.get("date"),
				"amount": float(it.get("amount", 0.0)),
				"merchant": it.get("merchant"),
				"category": it.get("category") or "uncategorized",
				"notes": it.get("notes"),
				"pending": bool(it.get("pending", False)),
				"created_at": datetime.utcnow()
			})
		if prepared:
			await self.transactions.insert_many(prepared)
		return {"imported": len(prepared)}

	async def list_transactions(
		self,
		user_id: str,
		account_id: Optional[str] = None,
		category: Optional[str] = None,
		start: Optional[str] = None,
		end: Optional[str] = None,
		limit: int = 200
	) -> List[Dict[str, Any]]:
		query: Dict[str, Any] = {"user_id": user_id}
		if account_id:
			query["account_id"] = account_id
		if category:
			query["category"] = category
		if start or end:
			date_filter: Dict[str, Any] = {}
			if start:
				date_filter["$gte"] = datetime.fromisoformat(start.replace("Z", "+00:00"))
			if end:
				date_filter["$lte"] = datetime.fromisoformat(end.replace("Z", "+00:00"))
			query["date"] = date_filter

		results: List[Dict[str, Any]] = []
		cursor = self.transactions.find(query).sort("date", -1).limit(limit)
		async for doc in cursor:
			doc["_id"] = str(doc["_id"])
			results.append(doc)
		return results

	# Summaries
	async def spending_summary_by_category(self, user_id: str, month: Optional[str] = None) -> List[Dict[str, Any]]:
		"""
		Sum of negative amounts (spend) grouped by category.
		month format: 'YYYY-MM' (UTC)
		"""
		match: Dict[str, Any] = {"user_id": user_id}
		if month:
			year, mon = month.split("-")
			start = datetime(int(year), int(mon), 1)
			if int(mon) == 12:
				end = datetime(int(year) + 1, 1, 1)
			else:
				end = datetime(int(year), int(mon) + 1, 1)
			match["date"] = {"$gte": start, "$lt": end}

		pipeline = [
			{"$match": match},
			{"$match": {"amount": {"$lt": 0}}},  # expenses
			{"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
			{"$project": {"category": "$_id", "total": 1, "_id": 0}},
			{"$sort": {"total": 1}}
		]
		cursor = self.transactions.aggregate(pipeline)
		results: List[Dict[str, Any]] = []
		async for doc in cursor:
			results.append(doc)
		return results

	async def cashflow_summary(self, user_id: str, month: Optional[str] = None) -> Dict[str, float]:
		"""
		Returns {"income": X, "expenses": Y, "net": X+Y}, where expenses negative.
		"""
		match: Dict[str, Any] = {"user_id": user_id}
		if month:
			year, mon = month.split("-")
			start = datetime(int(year), int(mon), 1)
			if int(mon) == 12:
				end = datetime(int(year) + 1, 1, 1)
			else:
				end = datetime(int(year), int(mon) + 1, 1)
			match["date"] = {"$gte": start, "$lt": end}

		pipeline = [
			{"$match": match},
			{"$group": {
				"_id": None,
				"income": {"$sum": {"$cond": [{"$gt": ["$amount", 0]}, "$amount", 0]}},
				"expenses": {"$sum": {"$cond": [{"$lt": ["$amount", 0]}, "$amount", 0]}},
			}},
			{"$project": {"_id": 0, "income": 1, "expenses": 1, "net": {"$add": ["$income", "$expenses"]}}}
		]
		cursor = self.transactions.aggregate(pipeline)
		doc = await cursor.to_list(length=1)
		if not doc:
			return {"income": 0.0, "expenses": 0.0, "net": 0.0}
		result = doc[0]
		return {
			"income": float(result.get("income", 0.0)),
			"expenses": float(result.get("expenses", 0.0)),
			"net": float(result.get("net", 0.0))
		}


