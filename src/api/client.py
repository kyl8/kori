import httpx
import asyncio

class APIClient:
    """initializes client for making api requests"""
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def get(self, endpoint: str, params: dict):
        response = await self.client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    async def post(self, endpoint: str, data: dict):
        response = await self.client.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()


class APIManager:
    """manages multiple api clients"""
    def __init__(self):
        from .anilist import AniListClient
        from .anizip import AniZipClient
        
        self.anilist = AniListClient()
        self.anizip = AniZipClient()

    async def close(self):
        await asyncio.gather(
            self.anilist.close(),
            self.anizip.close()
        )


