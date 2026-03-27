import re
from urllib.parse import urlparse
from config import EMAIL_REGEX

PHONE_REGEX = r"\+?\d[\d\s\-\(\)]{8,}\d"

# Emails that belong to platforms/directories, not to the actual supplier
# Uses base names (without TLD) so we catch yellowpages.com, yellowpages.com.vn, etc.
JUNK_EMAIL_DOMAINS = [
    "yellowpages.com", "volza.com", "eximpedia.app", "trademo.com",
    "tradekey.com", "alibaba.com", "indiamart.com", "made-in-china.com",
    "globalsources.com", "chanchao.com.tw", "auspost.com.au",
    "state.gov", "kita.net", "serpapi.com", "google.com",
    "example.com", "nbd.ltd", "zauba.com", "ipavietnam.org",
]

# Base names to catch country-specific variants (e.g. yellowpages.com.vn)
_JUNK_EMAIL_BASE_NAMES = [
    "yellowpages", "volza", "eximpedia", "trademo", "tradekey",
    "alibaba", "indiamart", "globalsources", "auspost",
]

def _is_junk_email(email):
    """Check if an email belongs to a known platform/directory rather than a supplier."""
    domain = email.split("@")[-1].lower()

    # Exact match or subdomain match (e.g. mail.yellowpages.com)
    for junk in JUNK_EMAIL_DOMAINS:
        if domain == junk or domain.endswith("." + junk):
            return True

    # Base name match to catch country TLD variants (e.g. yellowpages.com.vn)
    domain_parts = domain.split(".")
    if domain_parts:
        base = domain_parts[0]
        if base in _JUNK_EMAIL_BASE_NAMES:
            return True

    return False

def filter_emails_by_website(emails, website):
    """
    Prefer emails whose domain matches the supplier's website domain.
    If none match, return non-junk emails. If all are junk, return empty.
    """
    if not emails:
        return []

    # Remove junk platform emails first
    emails = [e for e in emails if not _is_junk_email(e)]
    if not emails:
        return []

    if not website:
        return emails

    # Extract website domain (e.g. "vichem.vn" from "https://vichem.vn/some/path")
    try:
        site_domain = urlparse(website).netloc.lower()
        # Remove www. prefix
        site_domain = site_domain.removeprefix("www.")
    except Exception:
        return emails

    # Split into matching and non-matching
    matching = [e for e in emails if site_domain and site_domain in e.split("@")[-1]]
    return matching if matching else emails

# Valid TLDs are 2-4 letter alphabetic strings (.com, .vn, .info)
# Rejects .phone (5), .website (7), etc. which are usually regex over-matches
_VALID_TLD_PATTERN = re.compile(r'\.[a-zA-Z]{2,4}$')
# Reject emails where the local part looks like a label prefix (e.g. "emaildirector@")
_JUNK_LOCAL_PREFIXES = ["email", "fax", "tel", "phone", "website", "url"]

def _is_valid_email(email):
    """Check that an email has a plausible TLD and local part."""
    domain = email.split("@")[-1]
    local = email.split("@")[0]

    # TLD must be 2-6 alphabetic chars (rejects .phone, .12345, etc.)
    if not _VALID_TLD_PATTERN.search(domain):
        return False

    # Reject if local part is just a label word (e.g. "emaildirector", "faxnumber")
    for prefix in _JUNK_LOCAL_PREFIXES:
        if local == prefix or local.startswith(prefix + "director") or local.startswith(prefix + "number"):
            return False

    return True

def extract_emails(text):
    """
    Extract all unique emails from a given text and strip trailing punctuation.
    """
    if not text:
        return []

    emails = re.findall(EMAIL_REGEX, text)
    # Clean up: strip common trailing punctuation often caught by regex in snippets
    emails = [e.lower().rstrip('.,;:') for e in emails]
    # Remove junk platform emails and invalid emails
    emails = [e for e in emails if _is_valid_email(e) and not _is_junk_email(e)]
    return list(set(emails))

def extract_phones(text):
    """
    Extract unique phone numbers and exclude date-like strings.
    """
    if not text:
        return []

    phones = re.findall(PHONE_REGEX, text)
    cleaned_phones = []
    
    for p in phones:
        # Clean: remove extra whitespace and strip punctuation
        p_clean = re.sub(r'\s+', ' ', p).strip().rstrip('.,;:')
        
        # Exclude dates (e.g., 01-10-2024 or 2024/10/01)
        if re.search(r'\d{1,4}[-/]\d{1,4}[-/]\d{1,4}', p_clean):
            continue
            
        # Filter out short or obviously wrong strings
        if len(p_clean) > 8:
            cleaned_phones.append(p_clean)
            
    return list(set(cleaned_phones))

def extract_contact_info(search_results):
    """
    Extract supplier name, website, and contact info from search results.
    """
    extracted_data = []

    for result in search_results:
        title = result.get("title", "")
        link = result.get("link", "")
        snippet = result.get("snippet", "")

        # Try to find the company name if title is too short, generic, or just the material
        supplier_name = title
        lower_title = title.lower()
        generic_terms = ["contact us", "about us", "home", "our business", "profile", "manufacturing", "export co"]
        
        if len(title.split()) <= 2 or any(x in lower_title for x in generic_terms) or any(x in lower_title for x in ["resins", "plastic", "supplier"]):
             # Look for "Company Name Ltd" or similar in the snippet (improved regex)
             # Try to catch uppercase patterns like "LONG SON PETROCHEMICALS" or "Bao Ma Co., Ltd"
             patterns = [
                 r'([A-Z\d][\w\s\.]+(?:Co\.|Ltd\.|JSC|Corp\.|Inc\.|Group|Company|Factory))',
                 r'\b([A-Z]{3,}(?:\s[A-Z]{3,})+)\b' # Two or more all-caps words
             ]
             for pattern in patterns:
                 match = re.search(pattern, snippet)
                 if match:
                     potential_name = match.group(0).strip()
                     # Final check: exclude if it contains conversational junk or is too long (likely a sentence)
                     lower_p = potential_name.lower()
                     if any(x in lower_p for x in ["hello", "good morning", "welcome", "about us", "wish you"]):
                         continue
                         
                     if len(potential_name.split()) >= 2 and len(potential_name) < 60: 
                         supplier_name = potential_name
                         break

        # Extract info from snippet and title
        emails = extract_emails(f"{title} {snippet}")
        emails = filter_emails_by_website(emails, link)
        phones = extract_phones(f"{title} {snippet}")

        extracted_data.append({
            "Supplier Name": supplier_name,
            "Website": link,
            "Emails": ", ".join(emails) if emails else "Not Found",
            "Phones": ", ".join(phones) if phones else "Not Found",
            "Snippet": snippet
        })

    return extracted_data
