"""Tool: airport lookup. Turns a city or code into airport codes (no network needed).

Cities with several airports (New York, London, ...) return all of them, so the
search can compare nearby airports. Extend AIRPORTS to cover more cities.
"""

# code: (city, country)
AIRPORTS = {
    "ATL": ("Atlanta", "US"), "BOS": ("Boston", "US"), "ORD": ("Chicago", "US"), "MDW": ("Chicago", "US"),
    "DFW": ("Dallas", "US"), "DAL": ("Dallas", "US"), "DEN": ("Denver", "US"), "DTW": ("Detroit", "US"),
    "IAH": ("Houston", "US"), "HOU": ("Houston", "US"), "LAS": ("Las Vegas", "US"),
    "LAX": ("Los Angeles", "US"), "BUR": ("Los Angeles", "US"), "LGB": ("Los Angeles", "US"),
    "MIA": ("Miami", "US"), "FLL": ("Miami", "US"), "MSP": ("Minneapolis", "US"),
    "JFK": ("New York", "US"), "LGA": ("New York", "US"), "EWR": ("New York", "US"),
    "MCO": ("Orlando", "US"), "PHL": ("Philadelphia", "US"), "PHX": ("Phoenix", "US"),
    "PDX": ("Portland", "US"), "SAN": ("San Diego", "US"), "SFO": ("San Francisco", "US"),
    "OAK": ("San Francisco", "US"), "SJC": ("San Jose", "US"), "SEA": ("Seattle", "US"),
    "SLC": ("Salt Lake City", "US"), "IAD": ("Washington", "US"), "DCA": ("Washington", "US"),
    "BWI": ("Washington", "US"), "HNL": ("Honolulu", "US"), "AUS": ("Austin", "US"),
    "YYZ": ("Toronto", "CA"), "YVR": ("Vancouver", "CA"), "MEX": ("Mexico City", "MX"),
    "CUN": ("Cancun", "MX"), "LHR": ("London", "GB"), "LGW": ("London", "GB"), "STN": ("London", "GB"),
    "CDG": ("Paris", "FR"), "ORY": ("Paris", "FR"), "AMS": ("Amsterdam", "NL"), "FRA": ("Frankfurt", "DE"),
    "MAD": ("Madrid", "ES"), "BCN": ("Barcelona", "ES"), "FCO": ("Rome", "IT"), "DUB": ("Dublin", "IE"),
    "IST": ("Istanbul", "TR"), "DXB": ("Dubai", "AE"), "DOH": ("Doha", "QA"),
    "NRT": ("Tokyo", "JP"), "HND": ("Tokyo", "JP"), "KIX": ("Osaka", "JP"), "ICN": ("Seoul", "KR"),
    "PEK": ("Beijing", "CN"), "PVG": ("Shanghai", "CN"), "HKG": ("Hong Kong", "HK"),
    "TPE": ("Taipei", "TW"), "SIN": ("Singapore", "SG"), "BKK": ("Bangkok", "TH"),
    "SGN": ("Ho Chi Minh City", "VN"), "HAN": ("Hanoi", "VN"), "DAD": ("Da Nang", "VN"),
    "MNL": ("Manila", "PH"), "KUL": ("Kuala Lumpur", "MY"), "DEL": ("Delhi", "IN"), "BOM": ("Mumbai", "IN"),
    "SYD": ("Sydney", "AU"), "MEL": ("Melbourne", "AU"), "AKL": ("Auckland", "NZ"),
}

# Other names people use for the same city
ALIASES = {
    "nyc": "New York", "new york city": "New York", "la": "Los Angeles", "sf": "San Francisco",
    "bay area": "San Francisco", "vegas": "Las Vegas", "dc": "Washington", "washington dc": "Washington",
    "saigon": "Ho Chi Minh City", "hcmc": "Ho Chi Minh City", "philly": "Philadelphia",
    "chi": "Chicago", "tokyo city": "Tokyo",
}


def lookup_airport(text: str) -> tuple[list[str], str] | None:
    """Return (airport_codes, city_label) for a city/code, or None if unknown."""
    if not text:
        return None
    t = text.strip()
    code = t.upper()
    # "New York (JFK)" or "JFK" -> use the code exactly as given
    for token in code.replace("(", " ").replace(")", " ").replace(",", " ").split():
        if token in AIRPORTS and len(token) == 3:
            return [token], f"{AIRPORTS[token][0]} ({token})"
    name = ALIASES.get(t.lower(), t)
    name_lower = name.lower()
    matches = [c for c, (city, _) in AIRPORTS.items() if city.lower() == name_lower]
    if not matches:  # partial match, e.g. "London, UK"
        matches = [c for c, (city, _) in AIRPORTS.items() if city.lower() in name_lower]
    if not matches:
        return None
    city = AIRPORTS[matches[0]][0]
    return matches, f"{city} ({', '.join(matches)})"


def is_known_code(code: str) -> bool:
    return code.upper() in AIRPORTS


def same_place(code: str, allowed_codes: list[str]) -> bool:
    """True if `code` is one of the allowed airports or in the same city."""
    code = (code or "").upper()
    if code in allowed_codes:
        return True
    cities = {AIRPORTS[c][0] for c in allowed_codes if c in AIRPORTS}
    return code in AIRPORTS and AIRPORTS[code][0] in cities
