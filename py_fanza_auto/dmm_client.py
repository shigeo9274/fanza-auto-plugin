from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import requests


@dataclass
class DMMClient:
    api_id: str
    affiliate_id: str
    base: str = "https://api.dmm.com/affiliate/v3"
    timeout: int = 30

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base}/{path}"
        res = requests.get(url, params=params, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

    def item_list(
        self,
        site: str,
        service: str,
        floor: str,
        keyword: str = "",
        sort: str = "date",
        gte_date: Optional[str] = None,
        lte_date: Optional[str] = None,
        article: Optional[str] = None,
        article_id: Optional[str] = None,
        hits: int = 100,
        offset: int = 1,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "api_id": self.api_id,
            "affiliate_id": self.affiliate_id,
            "site": site,
            "service": service,
            "floor": floor,
            "keyword": keyword,
            "sort": sort,
            "output": "json",
            "hits": hits,
            "offset": offset,
        }
        if article and article_id:
            params["article"] = article
            params["article_id"] = article_id
        if gte_date:
            params["gte_date"] = gte_date
        if lte_date:
            params["lte_date"] = lte_date
        return self._get("ItemList", params)

    def floor_list(self) -> Dict[str, Any]:
        params = {"api_id": self.api_id, "affiliate_id": self.affiliate_id, "output": "json"}
        return self._get("FloorList", params)

    def actress_search(self, actress_id: str) -> Dict[str, Any]:
        params = {
            "api_id": self.api_id,
            "affiliate_id": self.affiliate_id,
            "actress_id": actress_id,
            "hits": 1,
            "offset": 1,
            "sort": "id",
            "output": "json",
        }
        return self._get("ActressSearch", params)

