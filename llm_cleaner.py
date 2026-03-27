import json
from groq import Groq
from config import GROQ_API_KEY


def extract_company_names(suppliers, material, country):
    """
    Sends all cleaned suppliers to Groq in ONE batch call.
    Uses website URL, current name, and snippet to determine the real company name.
    Returns only validated suppliers with proper names.
    """
    if not GROQ_API_KEY:
        print("Warning: GROQ_API_KEY not set. Skipping LLM name extraction.")
        return suppliers

    if not suppliers:
        return suppliers

    # Build compact entries — only send what the LLM needs
    entries = []
    for i, s in enumerate(suppliers):
        entries.append({
            "id": i,
            "name": s.get("Supplier Name", ""),
            "url": s.get("Website", ""),
            "snippet": (s.get("Snippet", "") or "")[:100],
        })

    # Split into batches of 25 to stay within token limits
    batch_size = 25
    all_name_map = {}

    for batch_start in range(0, len(entries), batch_size):
        batch = entries[batch_start:batch_start + batch_size]

        prompt = f"""You are a procurement data assistant. I searched for "{material}" suppliers in "{country}".

Below are search results. For each, determine the REAL company name.

Rules:
- Use the url domain and snippet to identify the actual company
- Return a clean company name (e.g. "Cosmo Films Ltd" not "cosmofilms")
- If the current name already looks correct, keep it
- If the result is NOT a real {material} supplier/manufacturer/distributor (e.g. pet store, movie, marketplace, news, blog, directory, government site), set name to null
- Return ONLY a valid JSON array, no markdown

Input:
{json.dumps(batch, ensure_ascii=False)}

Return format:
[{{"id": 0, "name": "Company Name or null"}}]"""

        try:
            response = _call_groq(prompt)
            batch_map = _parse_response(response)
            all_name_map.update(batch_map)
        except Exception as e:
            print(f"  Warning: Groq batch error: {e}. Keeping original names for this batch.")
            for entry in batch:
                all_name_map[entry["id"]] = entry["name"]

    # Update supplier names and filter out nulls
    updated = []
    for i, s in enumerate(suppliers):
        if i in all_name_map and all_name_map[i]:
            s["Supplier Name"] = all_name_map[i]
            updated.append(s)

    print(f"  LLM validated {len(updated)}/{len(suppliers)} as real suppliers")
    return updated

def _call_groq(prompt):
    """Make a single Groq API call."""
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip()


def _parse_response(raw):
    """Parse LLM JSON response into a {id: name} map."""
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    results = json.loads(raw)
    return {r["id"]: r["name"] for r in results if r.get("name")}
