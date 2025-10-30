from .client import APIClient

class AniZipClient(APIClient):
    def __init__(self):
        super().__init__("https://api.ani.zip/mappings")

    async def get_mappings(self, anilist_id: int):
        """get ani.zip mappings for a given anilist id"""

        response = await self.get("", params={"anilist_id": anilist_id})
        return response
    
    def is_regular_episode(self, episode_key: str) -> bool:
        """specials episode have non-numeric letters like "S01", "S02", etc."""

        return episode_key.isdigit()

    def extract_episode_info(self, episode_data: dict, anime_id: int) -> dict:
        """
        extract episode number, anime ID, and synopsis from episode data 
        """
        episode_number = episode_data.get("episode")
        synopsis = episode_data.get("summary") or episode_data.get("overview")
        
        return {
            "episode_title": episode_data.get("title", {}).get("en") or episode_data.get("title", {}).get("x-jat") or "N/A",
            "episode_number": episode_number,
            "anime_id": anime_id,
            "synopsis": synopsis
        }
    
    def extract_all_episodes_info(self, episodes_data: dict, anime_id: int) -> list:
        """
        extract episode information from all episodes (only regular episodes, no specials)
        """
        result = []
        for episode_key, episode_data in episodes_data.items():
            if self.is_regular_episode(episode_key):
                info = self.extract_episode_info(episode_data, anime_id)
                if info["synopsis"]:
                    result.append(info)
                else:
                    pass
        return result

