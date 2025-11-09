from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import feedparser  # type: ignore
import aiohttp

try:
	from duckduckgo_search import DDGS  # type: ignore
	_DDG_AVAILABLE = True
except Exception:
	_DDG_AVAILABLE = False


FINANCE_RSS = [
	("Yahoo Finance - Top Stories", "https://finance.yahoo.com/news/rssindex"),
	("Reuters - Business", "http://feeds.reuters.com/reuters/businessNews"),
	("CNBC - Top News", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
]


def _parse_entry(src_title: str, entry: Any) -> Dict[str, Any]:
	published = None
	if hasattr(entry, "published_parsed") and entry.published_parsed:
		published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
	return {
		"source": src_title,
		"title": getattr(entry, "title", ""),
		"link": getattr(entry, "link", ""),
		"summary": getattr(entry, "summary", ""),
		"published": published,
	}


async def fetch_rss() -> List[Dict[str, Any]]:
	articles: List[Dict[str, Any]] = []
	for src_title, url in FINANCE_RSS:
		try:
			feed = feedparser.parse(url)
			for entry in getattr(feed, "entries", []):
				articles.append(_parse_entry(src_title, entry))
		except Exception:
			continue
	return articles


async def ddg_news_search(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
	if not _DDG_AVAILABLE:
		return []
	results: List[Dict[str, Any]] = []
	try:
		with DDGS() as ddgs:
			for item in ddgs.news(keywords=query, max_results=max_results, timelimit="7d"):
				results.append({
					"source": item.get("source"),
					"title": item.get("title"),
					"link": item.get("url"),
					"summary": item.get("body"),
					"published": item.get("date"),
				})
	except Exception:
		pass
	return results


async def web_page_title(session: aiohttp.ClientSession, url: str) -> Optional[str]:
	try:
		async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
			if resp.status != 200:
				return None
			text = await resp.text()
			# naive title extraction
			start = text.find("<title>")
			end = text.find("</title>", start + 7)
			if start != -1 and end != -1:
				return text[start + 7:end].strip()
	except Exception:
		return None
	return None


async def enrich_titles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	async with aiohttp.ClientSession() as session:
		tasks = []
		for a in articles:
			if not a.get("title") and a.get("link"):
				tasks.append(web_page_title(session, a["link"]))
			else:
				tasks.append(asyncio.sleep(0, result=None))
		results = await asyncio.gather(*tasks, return_exceptions=True)
	for a, t in zip(articles, results):
		if t and not a.get("title"):
			a["title"] = t
	return articles


async def aggregate_news(query: Optional[str] = None, symbols: Optional[List[str]] = None, max_results: int = 50) -> List[Dict[str, Any]]:
	base = await fetch_rss()
	enriched: List[Dict[str, Any]] = base

	if query:
		search_results = await ddg_news_search(query, max_results=max_results)
		enriched.extend(search_results)

	if symbols:
		for sym in symbols:
			search_results = await ddg_news_search(f"{sym} stock", max_results=max_results // max(1, len(symbols)))
			enriched.extend(search_results)

	# Deduplicate by link
	seen = set()
	deduped: List[Dict[str, Any]] = []
	for a in enriched:
		link = a.get("link")
		if not link or link in seen:
			continue
		seen.add(link)
		deduped.append(a)

	# Sort by published desc when available
	def _sort_key(a: Dict[str, Any]):
		ts = a.get("published")
		try:
			return datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else datetime.min
		except Exception:
			return datetime.min
	deduped.sort(key=_sort_key, reverse=True)
	return deduped[:max_results]


async def web_search(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
	"""
	General web search via DuckDuckGo; returns list of {"title","link","snippet"}.
	"""
	if not _DDG_AVAILABLE:
		return []
	items: List[Dict[str, Any]] = []
	try:
		with DDGS() as ddgs:
			for r in ddgs.text(keywords=query, max_results=max_results, region="us-en"):
				items.append({
					"title": r.get("title"),
					"link": r.get("href") or r.get("url"),
					"snippet": r.get("body"),
					"source": "ddg",
				})
	except Exception:
		pass
	return items


