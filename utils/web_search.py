"""
Web Search Utility — Search and fetch from the web
Uses Serper API (Google Search) with BeautifulSoup for content extraction.
"""

import os
import requests
from bs4 import BeautifulSoup
from typing import Optional
import time


SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")
SERPER_URL = "https://google.serper.dev/search"


def search_web(query: str, num_results: int = 5) -> list[dict]:
    """
    Search Google via Serper API.
    Returns list of {title, url, snippet} dicts.
    """
    if not SERPER_API_KEY:
        print("[web_search] WARNING: SERPER_API_KEY not set — returning empty results")
        return []

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": num_results, "hl": "en", "gl": "us"}

    try:
        resp = requests.post(SERPER_URL, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for r in data.get("organic", [])[:num_results]:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("link", ""),
                "snippet": r.get("snippet", ""),
            })
        return results
    except Exception as e:
        print(f"[web_search] Error: {e}")
        return []


def fetch_page_text(url: str, max_chars: int = 3000) -> str:
    """
    Fetch a URL and extract clean text (strips HTML, scripts, nav).
    Returns up to max_chars characters.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        # Clean up whitespace
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:max_chars]
    except Exception as e:
        print(f"[fetch_page] Error fetching {url}: {e}")
        return ""


def search_and_fetch(query: str, num_results: int = 3) -> list[dict]:
    """
    Search for query and fetch content from top results.
    Returns list of {title, url, snippet, content} dicts.
    """
    results = search_web(query, num_results)
    enriched = []
    for r in results:
        time.sleep(0.5)  # Rate limiting — be polite
        content = fetch_page_text(r["url"])
        enriched.append({**r, "content": content})
    return enriched


def get_pexels_media(query: str, media_type: str = "videos", per_page: int = 5) -> list[dict]:
    """
    Search Pexels for royalty-free images or videos.
    media_type: "videos" or "photos"
    Returns list of {id, url, thumbnail, width, height} dicts.
    """
    pexels_key = os.getenv("PEXELS_API_KEY", "")
    if not pexels_key:
        print("[pexels] WARNING: PEXELS_API_KEY not set")
        return []

    base = "https://api.pexels.com/videos/search" if media_type == "videos" else "https://api.pexels.com/v1/search"
    headers = {"Authorization": pexels_key}
    params = {"query": query, "per_page": per_page, "orientation": "portrait" if media_type == "videos" else "landscape"}

    try:
        resp = requests.get(base, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        items = data.get("videos", data.get("photos", []))
        for item in items:
            if media_type == "videos":
                # Get the HD video file
                files = item.get("video_files", [])
                hd = next((f for f in files if f.get("quality") == "hd"), files[0] if files else None)
                results.append({
                    "id": item["id"],
                    "url": hd["link"] if hd else "",
                    "thumbnail": item.get("image", ""),
                    "width": item.get("width", 0),
                    "height": item.get("height", 0),
                    "duration": item.get("duration", 0),
                })
            else:
                results.append({
                    "id": item["id"],
                    "url": item["src"]["large"],
                    "thumbnail": item["src"]["medium"],
                    "width": item["width"],
                    "height": item["height"],
                })
        return results
    except Exception as e:
        print(f"[pexels] Error: {e}")
        return []
