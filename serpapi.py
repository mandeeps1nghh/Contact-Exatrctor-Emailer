import time
from ddgs import DDGS

def search_suppliers(query, num_results=10):
    """
    Search for suppliers using DuckDuckGo (free, no API key needed).
    Returns results in the same format as the old SerpAPI version:
      [{"title": ..., "link": ..., "snippet": ...}, ...]
    """
    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=num_results))

        # Map DuckDuckGo fields to match the format the rest of the code expects
        results = []
        for r in raw_results:
            results.append({
                "title": r.get("title", ""),
                "link": r.get("href", ""),
                "snippet": r.get("body", ""),
            })

        # Small delay to avoid rate limiting
        time.sleep(1.5)
        return results

    except Exception as e:
        print(f"Error searching for '{query}': {e}")
        return []
