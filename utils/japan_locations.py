"""Japan prefecture and major city coordinates for geocoding fallback."""

JAPAN_PREFECTURE_COORDINATES = {
    'OSAKA': {'lat': 34.6937, 'lon': 135.5023},
    'TOKYO': {'lat': 35.6762, 'lon': 139.6503},
    'KANAGAWA': {'lat': 35.4478, 'lon': 139.6425},
    'FUKUOKA': {'lat': 33.5902, 'lon': 130.4017},
    'KYOTO': {'lat': 35.0116, 'lon': 135.7681},
    'HOKKAIDO': {'lat': 43.0642, 'lon': 141.3469},
    'AICHI': {'lat': 35.1802, 'lon': 136.9066},
    'HYOGO': {'lat': 34.6913, 'lon': 135.1830},
    'SAITAMA': {'lat': 35.8616, 'lon': 139.6455},
    'CHIBA': {'lat': 35.6073, 'lon': 140.1063}
}

def get_prefecture_coordinates(address):
    """Extract prefecture from address and return its coordinates."""
    address_upper = address.upper()
    
    # Try to find matching prefecture
    for prefecture, coords in JAPAN_PREFECTURE_COORDINATES.items():
        if prefecture in address_upper:
            return coords['lat'], coords['lon']
            
    # Default to Tokyo if no match found
    return JAPAN_PREFECTURE_COORDINATES['TOKYO']['lat'], JAPAN_PREFECTURE_COORDINATES['TOKYO']['lon']
