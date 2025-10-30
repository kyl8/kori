from .client import APIClient

class AniListClient(APIClient):
    def __init__(self):
        super().__init__("https://graphql.anilist.co")

    async def query(self, query: str, variables: dict):
        """make a graphql query to the anilist api"""
        data = {
            "query": query,
            "variables": variables or {}
        }
        return await self.post("", data=data)
    
    async def search(self, title: str, limit: int = 10, page: int = 1):
        """search for animes by title with pagination"""
        query = """
        query ($search: String, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                    total
                    perPage
                    currentPage
                    lastPage
                    hasNextPage
                }
                media(search: $search, type: ANIME) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    description(asHtml: false)
                    episodes
                    averageScore
                }
            }
        }
        """
        variables = {
            "search": title,
            "page": page,
            "perPage": limit
        }
        response = await self.query(query, variables)
        page_info = response.get("data", {}).get("Page", {}).get("pageInfo", {})
        total_pages = page_info.get("lastPage", 1)
        items = response.get("data", {}).get("Page", {}).get("media", [])
        single_results = []
        for anime in items:
            single_results.append({
                "id": anime["id"],
                "title_romaji": anime["title"]["romaji"],
                "title_english": anime["title"]["english"],
                "title_native": anime["title"]["native"],
                "description": anime["description"],
                "episodes": anime["episodes"],
                "average_score": anime["averageScore"]
            })
        return single_results, total_pages
