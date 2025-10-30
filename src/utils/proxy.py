import httpx
import io
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple


def _constants_dir() -> Path:
    return Path(__file__).parent.parent / "constants"


def load_proxies() -> List[str]:
    """load proxies from `src/constants/proxies-valid.txt` or `src/constants/proxies.txt` as fallback"""
    constants = _constants_dir()
    valid_file = constants / "proxies-valid.txt"
    if valid_file.exists():
        try:
            with open(valid_file, 'r', encoding='utf-8') as f:
                out = [line.strip() for line in f if line.strip()]
                out = [p if p.startswith(("http://", "https://", "socks5://", "socks4://"))
                       else ("http://" + p) for p in out]
                print(f"✅ Loaded {len(out)} VALID proxies from {valid_file}")
                return out
        except Exception as e:
            print(f"⚠️ Error loading valid proxies: {e}")

    fallback_file = constants / "proxies.txt"
    if fallback_file.exists():
        try:
            with open(fallback_file, 'r', encoding='utf-8') as f:
                out = [line.strip() for line in f if line.strip()]
                out = [p if p.startswith(("http://", "https://", "socks5://", "socks4://"))
                       else ("http://" + p) for p in out]
                print(f"✅ Loaded {len(out)} proxies from {fallback_file}")
                return out
        except Exception as e:
            print(f"⚠️ Error loading proxies: {e}")
    else:
        print(f"⚠️ No proxies file found at {fallback_file}")

    return []

def _stopwords_zip_url() -> str:
    return "https://raw.githubusercontent.com/nltk/nltk_data/refs/heads/gh-pages/packages/corpora/stopwords.zip"


def download_stopwords_with_proxies(proxies: List[str], timeout: float = 10.0, fallback_proxy: Optional[str] = None) -> Optional[bytes]:
    url = _stopwords_zip_url()
    for idx, proxy in enumerate(proxies, 1):
        print(f"  [{idx}/{len(proxies)}] Trying proxy {proxy}...", end=" ")
        try:
            mounts = {
                "http://": httpx.HTTPTransport(proxy=proxy),
                "https://": httpx.HTTPTransport(proxy=proxy),
            }
            client = httpx.Client(mounts=mounts, timeout=timeout)
            try:
                resp = client.get(url, headers={"User-Agent": "stopwords-downloader"})
                resp.raise_for_status()
                print("✅ SUCCESS!")
                return resp.content
            finally:
                client.close()
        except Exception as e:
            print(f"❌ {str(e)[:60]}")
            continue

    print("🔄 Trying direct (no proxy)...", end=" ")
    try:
        client = httpx.Client(timeout=timeout)
        try:
            resp = client.get(url, headers={"User-Agent": "stopwords-downloader"})
            resp.raise_for_status()
            print("✅ SUCCESS!")
            return resp.content
        finally:
            client.close()
    except Exception as e:
        print(f"❌ {e}")

    if fallback_proxy:
        print(f"🔄 Trying fallback proxy {fallback_proxy}...", end=" ")
        try:
            mounts = {
                "http://": httpx.HTTPTransport(proxy=fallback_proxy),
                "https://": httpx.HTTPTransport(proxy=fallback_proxy),
            }
            client = httpx.Client(mounts=mounts, timeout=timeout)
            try:
                resp = client.get(url, headers={"User-Agent": "stopwords-downloader"})
                resp.raise_for_status()
                print("✅ SUCCESS!")
                return resp.content
            finally:
                client.close()
        except Exception as e:
            print(f"❌ {e}")

    return None


def extract_english_stopwords_from_zip_bytes(zip_bytes: bytes) -> List[str]:
    """extract english stopwords from zip bytes"""
    zip_buffer = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(zip_buffer, 'r') as z:
        english_file = None
        for name in z.namelist():
            if 'stopwords/english' in name:
                english_file = name
                break
        if not english_file:
            raise RuntimeError("English stopwords file not found inside ZIP")
        with z.open(english_file) as f:
            return [line.decode('utf-8').strip() for line in f if line.strip()]


def get_or_create_stopwords(cache_file: Optional[Path] = None, fallback_proxy: Optional[str] = None) -> List[str]:
    """check if stopwords.txt is cached if not download it"""
    constants = _constants_dir()
    if cache_file is None:
        cache_file = constants / "stopwords.txt"

    if cache_file.exists():
        try:
            print(f"🔍 Loading cached stopwords...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"⚠️ Could not read cached stopwords: {e}")

    proxies = load_proxies()
    zip_bytes = None
    if proxies:
        zip_bytes = download_stopwords_with_proxies(proxies, timeout=10.0, fallback_proxy=fallback_proxy)
    if not zip_bytes:
        zip_bytes = download_stopwords_with_proxies([], timeout=15.0, fallback_proxy=fallback_proxy)

    if zip_bytes:
        try:
            stopwords = extract_english_stopwords_from_zip_bytes(zip_bytes)
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    for w in stopwords:
                        f.write(w + "\n")
                print(f"✅ Cached {len(stopwords)} stopwords to {cache_file}")
            except Exception as e:
                print(f"⚠️ Could not write stopwords cache: {e}")
            return stopwords
        except Exception as e:
            print(f"⚠️ Failed to extract stopwords from ZIP: {e}")
    print("⚠️ Using built-in fallback stopwords list")
    return [
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
        'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
        'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
        'what', 'which', 'who', 'whom', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
        'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just',
        'don', 'should', 'now', 'a', 'about', 'above', 'after', 'again', 'against', 'am',
        'an', 'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being',
        'below', 'between', 'by', 'd', 'did', 'do', 'does', 'doing', 'down', 'during',
        'from', 'further', 'had', 'has', 'have', 'having', 'in', 'into', 'is', 'of',
        'off', 'on', 'once', 'or', 'out', 'over', 'such', 'that', 'the', 'then',
        'there', 'these', 'they', 'this', 'those', 'under', 'until', 'up', 'was', 'were',
        'where', 'while', 'with', 'to', 'if', 'before', 'after', 'while', 'during'
    ]
