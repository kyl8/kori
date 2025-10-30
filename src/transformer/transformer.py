import re
from typing import List, Optional
from src.utils.proxy import get_or_create_stopwords
from src.searcher.find import remove_html_tags
import numpy as np


ENGLISH_STOPWORDS = set(get_or_create_stopwords())

class Transformer:
    """
    tf-idf for transformer for anime recommendations.
    analyzes anime synopses and episodes summaries to find similar content.
    """
    
    def __init__(self, min_df: int = 1, max_df: float = 0.95):
        self.min_df = min_df
        self.max_df = max_df
        self.vocabulary = {}  
        self.idf_values = {}  
        self.document_count = 0
        self.is_fitted = False
        self.anime_cache = {}  # cache pra anime
        self.episodes_cache = {}  # cache pra episodios
        # iniciando api clients, util pra nao ficar criando novos clientes toda hora
        from src.api.client import APIManager
        self.api = APIManager()
        
    async def close_client(self):
        """close the api clients"""
        await self.api.close()

    async def get_anime_synopsis(self, anime_id: int, anime_title: Optional[str]):
        """
        fetch and return the synopsis for a given anime id.
        uses AniListClient to fetch anime data.
        """
        try:
            if anime_id in self.anime_cache:
                synopsis = self.anime_cache[anime_id].get("description")
                return remove_html_tags(synopsis) if synopsis else None
            try:
                if anime_title:
                    results = await self.api.anilist.search(anime_title, limit=5)
                    for anime in results:
                        if isinstance(anime, dict) and anime.get("id") == anime_id:
                            synopsis = anime.get("description")
                            # caching the result
                            self.anime_cache[anime_id] = anime
                            return remove_html_tags(synopsis) if synopsis else None
                else:
                    print(f"⚠️ Warning: Searching without anime title for ID {anime_id}")
            except Exception as e:
                print(f"❌ Error during anime search for ID {anime_id}: {e}")
            
            return None
        
        except Exception as e:
            print(f"❌ Error fetching synopsis for anime ID {anime_id}: {e}")
            return None

    async def get_episode_summary(self, anime_id: int, episode_number: int) -> Optional[str]:
        """
        fetch and return the summary for a given anime ID and episode number.
        uses AniZipClient to fetch episode data.
        """
        try:
            episode_key = str(episode_number)
            cache_key = f"{anime_id}_{episode_key}"
            if cache_key in self.episodes_cache:
                synopsis = self.episodes_cache[cache_key].get("synopsis")
                return remove_html_tags(synopsis) if synopsis else None
            try:
                response = await self.api.anizip.get_mappings(anime_id)
                if response and "episodes" in response:
                    episodes_data = response["episodes"]
                    if episode_key in episodes_data:
                        episode_data = episodes_data[episode_key]
                        synopsis = episode_data.get("summary") or episode_data.get("overview")
                        #caching
                        self.episodes_cache[cache_key] = {"synopsis": synopsis}
                        return remove_html_tags(synopsis) if synopsis else None
                    else:
                        print(f"⚠️ Episode {episode_number} not found for anime ID {anime_id}")
                        return None
                else:
                    print(f"⚠️ No episode data found for anime ID {anime_id}")
                    return None
            except Exception as e:
                print(f"❌ Error during episode fetch for anime ID {anime_id}, episode {episode_number}: {e}")
        except Exception as e:
            print(f"❌ Error fetching episode summary for anime ID {anime_id}, episode {episode_number}: {e}")
            return None

    async def preprocess(self, text: str) -> List[str]:
        """preprocess text: remove html, tokenize, remove stopwords, special chars, etc."""
        if not text or not isinstance(text, str):
            return []
        text = remove_html_tags(text)
        text = text.lower()
        text = re.sub(r'[^a-z\s]', '', text)
        import nltk
        tokens = nltk.wordpunct_tokenize(text)
        tokens = [token for token in tokens if token not in ENGLISH_STOPWORDS and len(token) >= 3]
        return tokens

    async def create_doc(self, anime_id: int, anime_title: str, handle_episodes: bool = False, dataset_synopsis: Optional[str] = None):
        """
        creates a document for the anime. If handle_episodes=True, includes synopsis + all episodes (uses API);
        if False, uses only the dataset synopsis (dataset_synopsis).
        """
        try:
            print(f"📚 Creating document for {anime_title} (handle_episodes={handle_episodes})...")
            if not handle_episodes and dataset_synopsis is not None:
                # usa a sinopse do dataset diretamente
                combined_document = dataset_synopsis
            else:
                # busca sinopse e episódios via api
                synopsis = await self.get_anime_synopsis(anime_id, anime_title)
                if not synopsis:
                    print(f"  ⚠️ Could not fetch synopsis for {anime_title}")
                    synopsis = ""
                else:
                    print(f"  ✅ Fetched synopsis ({len(synopsis)} chars)")
                combined_document = synopsis
                if handle_episodes:
                    episode_summaries = []
                    episode_num = 1
                    while True:
                        summary = await self.get_episode_summary(anime_id, episode_num)
                        if not summary:
                            break
                        episode_summaries.append(summary)
                        print(f"  ✅ Episode {episode_num}: {len(summary)} chars")
                        episode_num += 1
                    print(f"  📊 Total episodes fetched: {len(episode_summaries)}")
                    if episode_summaries:
                        combined_document += " " + " ".join(episode_summaries)
            preprocessed_tokens = await self.preprocess(combined_document)
            return preprocessed_tokens
        except Exception as e:
            print(f"❌ Error creating anime document for {anime_title}: {e}")
            return []
        
    async def transform(self, documents: List[List[str]]):
        """
        vectorize the docs using TF-IDF
        each document is a list of tokens
        """
        processed_docs = documents 
        vocab = set()
        for tokens in processed_docs:
            vocab.update(tokens)
        vocab = sorted(vocab)
        self.vocabulary = {word: idx for idx, word in enumerate(vocab)}
        self.document_count = len(processed_docs)
        
        # calcula df
        from collections import Counter
        df = Counter()
        for tokens in processed_docs:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] += 1

        # calcula idf
        import math
        self.idf_values = {}
        for word in vocab:
            doc_freq = df[word]
            if doc_freq < self.min_df:
                continue
            if doc_freq / self.document_count > self.max_df:
                continue
            self.idf_values[word] = math.log((1 + self.document_count) / (1 + doc_freq)) + 1

        # calcula tf-idf para cada documento
        tfidf_matrix = []
        for tokens in processed_docs:
            tf = Counter(tokens)
            doc_vec = []
            for word in self.idf_values:
                tf_val = tf[word]
                idf_val = self.idf_values[word]
                doc_vec.append(tf_val * idf_val)
            norm = np.linalg.norm(doc_vec)
            if norm > 0:
                doc_vec = [v / norm for v in doc_vec]
            tfidf_matrix.append(doc_vec)
        self.is_fitted = True
        return tfidf_matrix
    
    async def cosine_similarity(self, vec1, vec2):
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
            return 0.0
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        