import asyncio
import re
from src.api.anilist import AniListClient


def remove_html_tags(text: str) -> str:
    """remove html brackets from description text"""

    if not text:
        return text
    clean_text = re.sub(r'<[^>]+>', '', text)
    return clean_text


async def search_and_select_anime(anime_name: str, limit: int = 10) -> dict | None:
    """
    search for an anime by name and let the user select one from the results.
    user can navigate between pages and select from results.
    """
    client = AniListClient()
    current_page = 1
    
    try:
        while True:
            print(f"\n📺 Searching for '{anime_name}' (page {current_page})...\n")
            results = await client.search(anime_name, limit=limit, page=current_page)
            
            if not results:
                if current_page == 1:
                    print("❌ No animes found. Try a different name.")
                    return None
                else:
                    print("❌ No more results on this page.")
                    current_page -= 1
                    continue
            
            print("📋 Results found:\n")
            for idx, anime in enumerate(results, 1):
                if isinstance(anime, dict):
                    title = anime.get("title_english") or anime.get("title_romaji") or anime.get("title_native")
                else:
                    title = str(anime)
                episodes = anime["episodes"] if isinstance(anime, dict) and "episodes" in anime else "?"
                score = anime["average_score"] if isinstance(anime, dict) and "average_score" in anime else "N/A"
                
                print(f"  {idx}. {title}")
                print(f"     Episodes: {episodes} | Score: {score}")
                if isinstance(anime, dict) and anime.get("description"):
                    description = anime.get("description") or ""
                    description = remove_html_tags(description)
                    description_preview = description[:150].replace("\n", " ").strip() + "..."
                    print(f"     {description_preview}")
                print()
            
            print("-" * 60)
            print(f"📄 Page {current_page} | Results on this page: {len(results)}")
            print("Commands:")
            print("  1-{}: Select anime by number".format(len(results)))
            print("  'n': Next page")
            print("  'p': Previous page")
            print("  'q': Quit")
            print("-" * 60)
            
            while True:
                try:
                    choice = input("\nEnter command: ").strip().lower()
                    
                    if choice == 'q':
                        print("Cancelled.")
                        return None
                    
                    elif choice == 'n':
                        print("\n⏭️  Loading next page...")
                        current_page += 1
                        break
                    
                    elif choice == 'p':
                        if current_page > 1:
                            print("\n⏮️  Loading previous page...")
                            current_page -= 1
                            break
                        else:
                            print("❌ You are already on the first page.")
                            continue
                    
                    else:
                        try:
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < len(results):
                                selected_anime = results[choice_idx]
                                if isinstance(selected_anime, dict):
                                    print(f"\n✅ Selected: {selected_anime['title_english'] or selected_anime['title_romaji']}")
                                    return selected_anime
                                else:
                                    print("❌ Unexpected result format. Please try again.")
                                    continue
                            else:
                                print(f"❌ Please enter a number between 1 and {len(results)}, or use n/p to navigate.")
                        
                        except ValueError:
                            print("❌ Invalid input. Use 1-{}, 'n', 'p', or 'q'.".format(len(results)))
                
                except KeyboardInterrupt:
                    print("\n\nCancelled.")
                    return None
    
    finally:
        await client.close()

