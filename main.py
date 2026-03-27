import uuid
from urllib.parse import urlparse
from queries import generate_queries
from serpapi import search_suppliers
from extractor import extract_contact_info, extract_emails, extract_phones, filter_emails_by_website
from cleaner import clean_supplier_data
from llm_cleaner import extract_company_names
from storage import save_to_csv


def _extract_domain_name(url):
    """Extract clean domain from URL for search queries (e.g. 'isffilm' from 'https://www.isffilm.com/')."""
    try:
        netloc = urlparse(url).netloc.lower().removeprefix("www.")
        return netloc.split(".")[0]  # just the main name part
    except Exception:
        return ""


def _deep_search_contacts(suppliers):
    """Search for contact info using clean company names and website domains."""
    for supplier in suppliers:
        name = supplier["Supplier Name"]
        website = supplier.get("Website", "")
        domain_name = _extract_domain_name(website)

        # Multiple query strategies to find contacts
        queries = [
            f'"{name}" email contact',
            f'{domain_name} contact email phone',
        ]

        print(f"  Searching contact for: {name}")
        for q in queries:
            contact_results = search_suppliers(q, num_results=3)

            for res in contact_results:
                text_to_scan = f"{res.get('title', '')} {res.get('snippet', '')}"

                new_emails = extract_emails(text_to_scan)
                new_emails = filter_emails_by_website(new_emails, website)
                current_emails = supplier["Emails"].split(", ") if supplier["Emails"] != "Not Found" else []
                combined_emails = list(set(current_emails + new_emails))
                supplier["Emails"] = ", ".join(combined_emails) if combined_emails else "Not Found"

                new_phones = extract_phones(text_to_scan)
                current_phones = supplier["Phones"].split(", ") if supplier["Phones"] != "Not Found" else []
                combined_phones = list(set(current_phones + new_phones))
                supplier["Phones"] = ", ".join(combined_phones) if combined_phones else "Not Found"

            # If we already found an email, skip the second query
            if supplier["Emails"] != "Not Found":
                break


def run_procurement_intelligence(material, country, request_id=None):
    """
    Main workflow for the Procurement Intelligence System.
    """
    if not request_id:
        request_id = str(uuid.uuid4())[:8]

    print(f"--- Starting Request: {request_id} ---")
    print(f"Material: {material}, Country: {country}")

    # 1. Generate Queries
    print("Generating queries...")
    queries = generate_queries(material, country)

    # 2. Search & Extract Suppliers
    all_suppliers = []
    print(f"Searching for suppliers via DuckDuckGo...")
    for query in queries:
        print(f"  Query: {query}")
        results = search_suppliers(query)
        extracted = extract_contact_info(results)
        all_suppliers.extend(extracted)

    # 3. Clean & Deduplicate Suppliers (basic junk domain/keyword filtering)
    print("Deduplicating suppliers...")
    cleaned_suppliers = clean_supplier_data(all_suppliers)

    # 4. Use Groq LLM to validate and extract proper company names (cap at 15)
    cleaned_suppliers = cleaned_suppliers[:15]
    print(f"Using LLM to validate {len(cleaned_suppliers)} suppliers...")
    validated_suppliers = extract_company_names(cleaned_suppliers, material, country)

    # 5. Deep Search: Find contacts using clean LLM-validated names
    print(f"Performing targeted contact search for {len(validated_suppliers)} verified suppliers...")
    _deep_search_contacts(validated_suppliers)

    # 6. Save to CSV
    print("Saving results...")
    csv_path = save_to_csv(validated_suppliers, f"suppliers_{request_id}.csv")

    print(f"--- Finished Request: {request_id} ---")
    print(f"Final result: {len(validated_suppliers)} verified suppliers saved to {csv_path}")
    return csv_path

if __name__ == "__main__":
    material = input("Enter Material (e.g. PET Film): ") or "PET Film"
    country = input("Enter Country (e.g. Vietnam): ") or "Vietnam"
    run_procurement_intelligence(material, country)
