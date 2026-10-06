"""Google Trends search for product demand signals in Ecuador.

Uses pytrends to get real search interest data.
"""

from __future__ import annotations

import asyncio
from src.shared.logger import logger


class TrendsSearch:
    """Query Google Trends for product demand in Ecuador."""

    async def get_trend_score(
        self,
        product_name: str,
        category: str = "",
        country: str = "EC",
    ) -> dict:
        """Get trend score for a product.

        Args:
            product_name: Product to search.
            category: Product category for context.
            country: ISO country code.

        Returns:
            Dict with trend_score (0.0-1.0), avg_interest, peak_interest, is_rising.
        """
        # Build search terms — short and generic
        words = product_name.lower().split()
        # Take first 2-3 meaningful words
        stopwords = {"de", "del", "la", "el", "los", "las", "en", "para", "con", "y", "x", "pcs"}
        keywords = [w for w in words if w not in stopwords][:3]
        search_term = " ".join(keywords)

        try:
            result = await asyncio.to_thread(self._query_trends, search_term, country)
            logger.info(
                f"[Trends] '{search_term}' in {country}: "
                f"score={result['trend_score']:.2f}, avg={result['avg_interest']:.0f}"
            )
            return result
        except Exception as e:
            logger.warning(f"[Trends] Failed for '{search_term}': {e}")
            return {"trend_score": 0.5, "avg_interest": 0, "peak_interest": 0, "is_rising": False, "search_term": search_term}

    def _query_trends(self, search_term: str, country: str) -> dict:
        """Synchronous trends query."""
        from pytrends.request import TrendReq

        pt = TrendReq(hl='es', tz=300, timeout=(5, 10))
        pt.build_payload([search_term], geo=country, timeframe='today 3-m')

        data = pt.interest_over_time()

        if data.empty:
            return {"trend_score": 0.3, "avg_interest": 0, "peak_interest": 0, "is_rising": False, "search_term": search_term}

        values = data.iloc[:, 0]
        avg = float(values.mean())
        peak = float(values.max())
        # Check if trend is rising (last 2 weeks vs first 2 weeks)
        recent = float(values[-14:].mean()) if len(values) >= 14 else avg
        early = float(values[:14].mean()) if len(values) >= 14 else avg
        is_rising = recent > early * 1.2  # 20% higher = rising

        # Normalize to 0.0-1.0 (Google Trends max is 100)
        # avg < 5 = very low demand, avg > 50 = high demand
        if avg <= 1:
            score = 0.1
        elif avg <= 5:
            score = 0.2 + (avg / 5) * 0.2  # 0.2-0.4
        elif avg <= 20:
            score = 0.4 + (avg / 20) * 0.2  # 0.4-0.6
        elif avg <= 50:
            score = 0.6 + (avg / 50) * 0.2  # 0.6-0.8
        else:
            score = 0.8 + min(avg / 100, 1.0) * 0.2  # 0.8-1.0

        # Bonus for rising trend
        if is_rising:
            score = min(score + 0.1, 1.0)

        return {
            "trend_score": round(score, 2),
            "avg_interest": round(avg, 1),
            "peak_interest": round(peak, 1),
            "is_rising": is_rising,
            "search_term": search_term,
        }
