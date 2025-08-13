import re
from typing import Tuple

def normalize_item_name(item_name: str) -> Tuple[str, int]:
    """
    Normalize item names and extract quantities.
    Returns tuple of (normalized_name, quantity)
    
    Examples:
    - "2x tacos" -> ("taco", 2)
    - "BURRITO" -> ("burrito", 1)
    - "3 Pizzas" -> ("pizza", 3)
    - "taco" -> ("taco", 1)
    """
    if not item_name:
        return "unknown", 1
    
    # Clean up the string
    cleaned = item_name.strip().lower()
    
    # Extract quantity patterns like "2x", "3 ", "2*", etc.
    quantity = 1
    
    # Pattern: "2x item", "3 x item", "4*item", etc.
    quantity_patterns = [
        r'^(\d+)\s*[x*×]\s*(.+)',  # "2x taco", "3 x taco", "4*taco"
        r'^(\d+)\s+(.+)',          # "2 tacos"
        r'(.+)\s*[x*×]\s*(\d+)$',  # "taco x 2"
        r'(.+)\s+(\d+)$',          # "taco 2"
    ]
    
    normalized_name = cleaned
    
    for pattern in quantity_patterns:
        match = re.match(pattern, cleaned)
        if match:
            groups = match.groups()
            if groups[0].isdigit():
                quantity = int(groups[0])
                normalized_name = groups[1].strip()
            elif groups[1].isdigit():
                normalized_name = groups[0].strip()
                quantity = int(groups[1])
            break
    
    # Normalize plural forms to singular
    normalized_name = singularize(normalized_name)
    
    # Additional cleanup
    normalized_name = re.sub(r'[^\w\s]', '', normalized_name)  # Remove special characters
    normalized_name = re.sub(r'\s+', ' ', normalized_name).strip()  # Normalize whitespace
    
    return normalized_name, quantity

def singularize(word: str) -> str:
    """
    Simple singularization for common food items.
    This is a basic implementation - could be enhanced with a proper library.
    """
    word = word.strip().lower()
    
    # Common food item mappings
    singular_map = {
        'tacos': 'taco',
        'burritos': 'burrito',
        'quesadillas': 'quesadilla',
        'nachos': 'nacho',
        'pizzas': 'pizza',
        'burgers': 'burger',
        'sandwiches': 'sandwich',
        'fries': 'fry',
        'chips': 'chip',
        'drinks': 'drink',
        'sodas': 'soda',
        'beers': 'beer',
        'cookies': 'cookie',
        'wings': 'wing',
        'ribs': 'rib',
        'steaks': 'steak',
        'salads': 'salad',
    }
    
    if word in singular_map:
        return singular_map[word]
    
    # Basic English pluralization rules
    if word.endswith('ies') and len(word) > 3:
        return word[:-3] + 'y'
    elif word.endswith('es') and len(word) > 2:
        if word.endswith(('ches', 'shes', 'xes', 'zes')):
            return word[:-2]
        return word[:-2]
    elif word.endswith('s') and len(word) > 1:
        return word[:-1]
    
    return word

def normalize_and_group_items(items: list) -> dict:
    """
    Take a list of item names and group them by normalized name with quantities.
    Returns dict with normalized names as keys and aggregated quantities as values.
    """
    grouped = {}
    
    for item_name in items:
        normalized, quantity = normalize_item_name(item_name)
        if normalized in grouped:
            grouped[normalized] += quantity
        else:
            grouped[normalized] = quantity
    
    return grouped

# Test cases for validation
def test_normalization():
    """Test function to validate normalization logic"""
    test_cases = [
        ("taco", ("taco", 1)),
        ("2x taco", ("taco", 2)),
        ("3 tacos", ("taco", 3)),
        ("BURRITO", ("burrito", 1)),
        ("4x BURRITOS", ("burrito", 4)),
        ("Pizza x 2", ("pizza", 2)),
        ("5 Pizzas!!!", ("pizza", 5)),
        ("chips & salsa", ("chips  salsa", 1)),
        ("", ("unknown", 1)),
    ]
    
    for input_item, expected in test_cases:
        result = normalize_item_name(input_item)
        print(f"Input: '{input_item}' -> Expected: {expected}, Got: {result}, Match: {result == expected}")

if __name__ == "__main__":
    test_normalization()