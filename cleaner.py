import re

def clean_supplier_name(name):
    """
    Remove common search engine junk from supplier names.
    """
    if not name:
        return ""

    # Reject names that are mostly non-Latin characters (Chinese, Arabic, etc.)
    # Real supplier names in our use case are in English/Latin script
    latin_chars = len(re.findall(r'[a-zA-Z]', name))
    total_alpha = len(re.findall(r'[^\s\d\W]', name, re.UNICODE))
    if total_alpha > 0 and latin_chars / total_alpha < 0.5:
        return ""

    # Remove everything after common separators (e.g. "Long Son Petrochemicals | Home")
    name = re.split(r' \| | - |: | – ', name)[0]

    # Remove trailing ellipses
    name = name.rstrip('. ')

    # Remove common junk suffixes (case insensitive)
    junk_suffixes = [
        "manufacturer", "supplier", "provider", "exporter", "distributor",
        "vendor", "factory", "wholesaler", "trader", "company", "official website"
    ]

    # Phrases that indicate a generic page title, not a company name
    generic_phrases = [
        "contact us", "about us", "home", "our business", "profile",
        "introduce", "mission", "vision", "welcome", "products", "product center",
        "news", "blog", "services", "careers", "sitemap", "legal",
        "privacy policy", "terms of use", "main market", "manufacturing",
        "export co", "about", "introduce", "brief features", "hello friends",
        "good morning", "industry report", "market outlook", "press release",
        "view complete", "toggle navigation", "logo", "life @", "recent developments",
        "getting to know", "we supply", "high quality polymer",
        "polymer injection", "plastic testing", "pp plastic standards",
        "aqueous polyolefin", "market size", "market was valued",
        "imports in", "exports in", "exports from", "exports under",
        "antidumping", "countervailing", "corrugated boxes",
        "acrylic resin dial", "viscocity improver",
        "co polymer suppliers",
    ]

    # Check if the name looks like a news headline or article title
    headline_verbs = [
        "to build", "surges", "invests", "signals", "aims to", "is set to",
        "announces", "arises", "ready for", "sought on", "petitions",
        "initiates", "investigation on", "inquiry on",
    ]
    for verb in headline_verbs:
        if verb in name.lower():
            return ""

    # Check if the name contains any generic phrases (partial match)
    name_check = name.lower().strip()
    for phrase in generic_phrases:
        if phrase in name_check:
            return ""

    # Clean up common SEO junk in product names (handles plurals too)
    for suffix in junk_suffixes:
        pattern = re.compile(rf'\b{suffix}s?\b', re.IGNORECASE)
        name = pattern.sub("", name).strip()

    # Remove trailing ellipses and punctuation
    name = name.rstrip('. ,;-')

    return name.strip()

def is_junk_result(name, website):
    """
    Check if a result is likely a directory, listicle, or report rather than a supplier.
    """
    name_lower = name.lower()
    website_lower = website.lower()

    # 1. Always-apply patterns — safe to match anywhere in the name
    always_junk_patterns = [
        r'^top \d+',                                    # "Top 10 suppliers..."
        r'\byellow\s*pages\b',                          # "Yellow Pages"
        r'\bhsn\s*code\b',                              # "HSN Code 3902"
        r'\b(anti.?dumping|countervailing)\b',          # trade law terms
        r'\bmarket\s+(report|size|outlook|was valued)\b',
        r'\bindustry\s+report\b',
        r'\bhow\s+to\b',
    ]
    for pattern in always_junk_patterns:
        if re.search(pattern, name_lower):
            return True

    # 2. Strict patterns — only apply when the name has NO corporate suffix
    #    This catches pure listing titles like "Suppliers of PET film in Vietnam"
    #    but lets through "ABC Corp - PET Film Supplier in Vietnam"
    has_company_indicator = bool(re.search(
        r'\b(Co\.?|Ltd\.?|JSC|Corp\.?|Inc\.?|Group|LLC|GmbH|Pte|S\.?A\.?|BV|AB|Joint.?Stock|Limited)\b',
        name, re.IGNORECASE
    ))
    if not has_company_indicator:
        listing_title_patterns = [
            r'\bsuppliers?\s+(of|in|for|from)\b',       # "Suppliers of PET film in Vietnam"
            r'\bmanufacturers?\s+(of|in|for|from)\b',    # "BOPET Film Manufacturers in Vietnam"
            r'\bdistributors?\s+(of|in|for|from)\b',
            r'\bexporters?\s+(of|in|for|from)\b',
            r'\bimporters?\s+(of|in|for|from)\b',
            r'\b(imports?|exports?)\s+(in|from|data)\b', # "Imports in Vietnam"
            r'^list\s+of\b',                             # "List of..." at start only
            r'\blist\s*$',                               # ends with "list"
        ]
        for pattern in listing_title_patterns:
            if re.search(pattern, name_lower):
                return True

    # 2. Simple keyword matches for remaining junk
    junk_keywords = [
        "research", "exploring", "versatility", "ranking", "directory",
        "b2b", "geniuses", "prestigious",
        "getting to know", "we supply", "recent developments",
        "good morning", "hello friends", "wish you",
        "management team", "plastic testing",
        "ad/cv duties", "corrugated boxes",
    ]
    for kw in junk_keywords:
        if kw in name_lower:
            return True

    # 3. Check website for common directory/informational domains
    junk_domains = [
        # Trade directories & databases
        "yellowpages", "exportgenius.in", "seair.co.in", "trademo.com",
        "tradekey.com", "b2bmap.com", "volza.com", "thetradevision.com",
        "tradewheel.com", "exportersindia.com", "indiamart.com", "alibaba.com",
        "made-in-china.com", "globalsources.com", "panjiva.com", "importyeti.com",
        "go4worldbusiness.com", "ec21.com", "ecvv.com", "fordaq.com",
        "zauba.com", "eximpedia.app", "en.nbd.ltd",
        "abrams.wiki", "company-listing.org",
        # Social media
        "youtube.com", "linkedin.com", "facebook.com", "instagram.com",
        "twitter.com", "x.com", "reddit.com",
        # News & media
        "wikipedia.org", "vnexpress.net", "vietnamplus.vn", "en.yna.co.kr",
        "theinvestor.co.kr", "pressreader.com", "chinaplasonline.com",
        "adsalecprj.com", "growyourbusiness.org",
        # Market research & reports
        "mordorintelligence.com", "techsciresearch.com", "6wresearch.com",
        # Government & legal
        "federalregister.gov", "govinfo.gov", "faegredrinker.com", "strtrade.com",
        "aslgate.com",
        # Academic
        "ncbi.nlm.nih.gov", "pmc.ncbi.nlm.nih.gov",
        # Job/people search
        "rocketreach.co", "zoominfo.com",
        # B2B noise & directories
        "globalscraps.com", "vietnamfactoryb2b.com", "world-business-guide.com",
        "investvietnam.vn", "chempoint.com",
        # Chinese/non-English platforms
        "zhihu.com", "baidu.com", "weibo.com", "bilibili.com",
        "163.com", "sohu.com", "sina.com.cn", "qq.com",
        # Retail / e-commerce / marketplaces
        "ebay.com", "ebay.co.uk", "amazon.com", "aliexpress.com",
        "petsmart.com", "petco.com", "walmart.com", "target.com",
        # Entertainment / media
        "tiktok.com", "dailymotion.com", "medium.com", "quora.com",
        "imdb.com", "rottentomatoes.com",
        # Other trade / export directories
        "tradekorea.com", "uservoice.com", "cantonfair.net", "ecer.com",
        "directliquidation.com", "kompass.com", "dnb.com",
        "thomasnet.com", "europages.com",
    ]

    for domain in junk_domains:
        if domain in website_lower:
            return True

    # 4. Check for obvious non-name patterns
    if len(name_lower) < 3 or name_lower.strip() in [
        "contact us", "about us", "home", "our business", "manufacturing",
        "co polymer", "slump keeper", "eva offgrade",
    ]:
        return True

    return False

def _looks_like_product_not_company(name):
    """
    Check if the name looks like a product description or technical term
    rather than a company name.
    """
    name_lower = name.lower().strip()

    # Product/chemical descriptions (no company would name itself this)
    product_patterns = [
        r"^(pp|pe|pvc|hdpe|ldpe|eva|abs|pet|safic|bopet)\s",  # starts with polymer abbreviation
        r"^(solid|liquid|aqueous|modified|high quality|surface|thermal|optical)\s",
        r"\b(resin|emulsion|monomer|co-polymer|copolymer|block polymer|homopolymer|pe wax)\b",
        r"^fr-\d+",                                     # government doc IDs
        r"^\d+\s*(kgs?|tons?|ltrs?)\b",                # quantities
        r"^(polypropylene|polyethylene|polyester|polyacetal|acrylic)\b",  # starts with polymer name
    ]
    for pattern in product_patterns:
        if re.search(pattern, name_lower):
            return True

    # Names that start with action/SEO words, not company names
    junk_prefixes = [
        "buy ", "sell ", "complete guide", "leading ", "chinese leading",
        "plastic sheets", "plastic rods", "plastic tubing",
        "international yellow",
    ]
    for prefix in junk_prefixes:
        if name_lower.startswith(prefix):
            return True

    return False

def _extract_root_domain(url):
    """
    Extract the root domain from a URL for deduplication.
    e.g. "https://www.chemtradeasia.vn/en/product" -> "chemtradeasia.vn"
    """
    from urllib.parse import urlparse
    try:
        netloc = urlparse(url).netloc.lower()
        # Remove www. prefix
        netloc = netloc.removeprefix("www.")
        # Extract root domain (last 2 parts, or 3 for co.uk style)
        parts = netloc.split(".")
        if len(parts) >= 3 and parts[-2] in ("co", "com", "org", "net", "gov"):
            return ".".join(parts[-3:])
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return netloc
    except Exception:
        return url.lower().strip("/")

def clean_supplier_data(data):
    """
    Deduplicate and clean supplier data, filtering out junk.
    """
    seen_domains = set()
    cleaned_data = []

    for entry in data:
        name = entry.get("Supplier Name", "")
        website = entry.get("Website", "").lower().strip("/")

        # Filter out junk results (listicles, directories, blogs)
        if is_junk_result(name, website):
            continue

        # Clean the name
        cleaned_name = clean_supplier_name(name)

        # Skip if name is now empty or too short
        if not cleaned_name or len(cleaned_name) < 3:
            continue

        # Skip product descriptions masquerading as company names
        if _looks_like_product_not_company(cleaned_name):
            continue

        entry["Supplier Name"] = cleaned_name

        # Deduplicate by root domain instead of full URL
        root_domain = _extract_root_domain(website)
        if root_domain and root_domain not in seen_domains:
            seen_domains.add(root_domain)
            cleaned_data.append(entry)

    return cleaned_data
