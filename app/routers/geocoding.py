from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, Dict, Any, List
import httpx
import json

from app.core.redis_client import get_redis

router = APIRouter(prefix="/geocode", tags=["geocoding"])

NOMINATIM_URL = "https://nominatim.openstreetmap.org"


@router.get("/search")
async def geocode_search(q: str = Query(...), limit: int = Query(10, ge=1, le=50)) -> List[Dict[str, Any]]:
	key = f"geocode:q:{q}:l:{limit}"
	r = await get_redis()
	cached = await r.get(key)
	if cached:
		return json.loads(cached)
	headers = {"User-Agent": "fiber-maps/1.0 (admin@example.com)"}
	params = {"q": q, "format": "jsonv2", "limit": str(limit), "addressdetails": 1}
	async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
		resp = await client.get(f"{NOMINATIM_URL}/search", params=params)
		if resp.status_code != 200:
			raise HTTPException(resp.status_code, "Geocoding failed")
		data = resp.json()
		await r.setex(key, 3600, json.dumps(data))
		return data


@router.get("/reverse")
async def geocode_reverse(lat: float, lon: float) -> Dict[str, Any]:
	key = f"geocode:rev:{lat:.6f},{lon:.6f}"
	r = await get_redis()
	cached = await r.get(key)
	if cached:
		return json.loads(cached)
	headers = {"User-Agent": "fiber-maps/1.0 (admin@example.com)"}
	params = {"lat": f"{lat}", "lon": f"{lon}", "format": "jsonv2", "addressdetails": 1}
	async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
		resp = await client.get(f"{NOMINATIM_URL}/reverse", params=params)
		if resp.status_code != 200:
			raise HTTPException(resp.status_code, "Reverse geocoding failed")
		data = resp.json()
		await r.setex(key, 3600, json.dumps(data))
		return data