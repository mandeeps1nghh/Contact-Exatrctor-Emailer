def generate_queries(material, country):
    """
    Generate a list of search queries based on the material and country.
    Optimized for DuckDuckGo — no Google-specific operators.
    """
    queries = [
        # Direct company searches
        f'"{material}" manufacturer {country} contact',
        f'"{material}" producer {country} company',
        f'"{material}" factory {country}',
        f'"{material}" supplier {country} email',
        f'"{material}" company {country} official website',

        # Role-specific searches
        f'"{material}" exporter {country}',
        f'"{material}" distributor {country}',
        f'"{material}" trading company {country}',

        # Slightly different phrasing to get different results
        f'{material} manufacturing company {country}',
        f'{material} production {country} Co Ltd',
        f'{material} {country} factory direct',
        f'{material} {country} wholesale supplier',

        # Industry-specific
        f'{material} {country} packaging company',
        f'{material} {country} industrial supply',
    ]
    return queries
