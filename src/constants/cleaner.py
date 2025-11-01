import pandas as pd
from pathlib import Path
from src.utils.remove_html_tags import remove_html_tags


def load_dataset(csv_path: str) -> pd.DataFrame:
    if csv_path is None:
        csv_path = Path(__file__).parent / "dataset.csv"
    df = pd.read_csv(csv_path)
    return df


#if some day i need it
def get_synopsis_by_title(anime_title: str, csv_path: str) -> dict | None:
    df = load_dataset(csv_path)
    mask = df['Name'].str.contains(anime_title, case=False, na=False)
    
    if mask.any():
        anime = df[mask].iloc[0]
        
        synopsis = anime.get('sypnopsis', '')
        synopsis = remove_html_tags(synopsis)
        
        return {
            'anime_id': anime['anime_id'],
            'title': anime['Name'],
            'synopsis': synopsis.strip()
        }
    
    return None


def get_all_synopses(csv_path: str, limit: int) -> list[dict]:
    df = load_dataset(csv_path)
    df = df.dropna(subset=['sypnopsis'])
    
    if limit:
        df = df.head(limit)
    
    results = []
    for _, anime in df.iterrows():
        synopsis = remove_html_tags(str(anime['sypnopsis']))
        
        results.append({
            'anime_id': anime['anime_id'],
            'title': anime['Name'],
            'synopsis': synopsis.strip()
        })
    
    return results
