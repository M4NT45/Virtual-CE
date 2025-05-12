import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from symspellpy import SymSpell, Verbosity
import pkg_resources

# Initialize components
lemmatizer = WordNetLemmatizer()

# Initialize SymSpell
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
dictionary_path = pkg_resources.resource_filename(
    "symspellpy", "frequency_dictionary_en_82_765.txt")
# Load dictionary
sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

# Marine engineering specific terms to preserve (won't be spell-checked)
marine_terms = {
    'hfo', 'mdo', 'lshfo', 'lsfo', 'vlsfo', 'mgb', 'mcr', 'rpm', 'turbocharger', 
    'scavenge', 'purifier', 'aux', 'auxiliary', 'mgo', 'lub', 'lube', 'fo', 'lo', 
    'kw', 'kwh', 'mlb', 'ppm', 'tbn', 'tbnb', 'hvac', 'me', 'ae', 'dg', 'genset', 
    'hvac', 'lpg', 'lng', 'co2', 'nox', 'sox', 'psi', 'mpa', 'bar', 'kpa',
    'crankcase', 'scavenging', 'crosshead', 'turbine', 'compressor', 'propeller',
    'injector', 'boiler', 'economizer', 'evaporator', 'viscosity', 'classifier', 
    'cooler', 'intercooler', 'aftercooler'
}

# Add common manufacturer names
manufacturer_terms = {
    'wartsila', 'man', 'sulzer', 'yanmar', 'caterpillar', 'cat', 'mak', 'bergen', 
    'rolls-royce', 'rolls', 'royce', 'mitsubishi', 'daihatsu', 'cummins', 'deutz', 
    'pielstick', 'abb', 'woodward', 'alfa', 'laval', 'alfalaval'
}

# Combine domain-specific terms
domain_terms = marine_terms.union(manufacturer_terms)

# Regex patterns for common formatting
unit_pattern = re.compile(r'(\d+)([a-zA-Z]+)')  # e.g., "10bar" -> "10 bar"
range_pattern = re.compile(r'(\d+)-(\d+)([a-zA-Z]+)')  # e.g., "10-15bar" -> "10-15 bar"

# Common marine engineering abbreviation expansion
abbreviations = {
    'temp': 'temperature',
    'aux': 'auxiliary',
    'lub': 'lubricating',
    'lube': 'lubricating',
    'fo': 'fuel oil',
    'lo': 'lubricating oil',
    'me': 'main engine',
    'ae': 'auxiliary engine',
    'dg': 'diesel generator',
    'fw': 'fresh water',
    'sw': 'sea water',
    't/c': 'turbocharger',
    'tc': 'turbocharger',
    'hx': 'heat exchanger',
    'cw': 'cooling water',
    'jw': 'jacket water',
    'ps': 'port side',
    'sb': 'starboard',
    'stbd': 'starboard',
    'hyd': 'hydraulic',
    'sys': 'system',
    'gen': 'generator',
    'alt': 'alternator',
    'pres': 'pressure',
    'prs': 'pressure',
    'press': 'pressure',
    'vib': 'vibration',
    'rpm': 'revolutions per minute',
    'rev': 'revolutions',
    'exh': 'exhaust',
    'prop': 'propeller',
    'eng': 'engine',
    'diff': 'differential',
    'temps': 'temperatures',
    'op': 'operating'
}

# Marine-specific corrections to add to dictionary
marine_corrections = {
    'purifyer': 'purifier',
    'purifiyer': 'purifier',
    'turbochargar': 'turbocharger',
    'exhoust': 'exhaust',
    'exaust': 'exhaust',
    'cylender': 'cylinder',
    'cilinder': 'cylinder',
    'comming': 'coming',
    'maintenence': 'maintenance',
    'maintenace': 'maintenance',
    'leakege': 'leakage',
    'shutingdown': 'shutting down',
    'diesal': 'diesel'
}

# Add marine-specific terms to the dictionary
for term in domain_terms:
    sym_spell.create_dictionary_entry(term, 1000)  # High frequency to prioritize

# Add corrections
for misspelled, correct in marine_corrections.items():
    sym_spell.create_dictionary_entry(correct, 1000)  # Ensure correct term is in dict

def spell_correct_word(word):
    """
    Correct spelling for a single word using SymSpell
    """
    # Skip spell checking for domain terms, short words, numbers, and words with digits
    if (word in domain_terms or 
        len(word) <= 2 or 
        word.isdigit() or 
        any(char.isdigit() for char in word)):
        return word
        
    # Handle contractions
    if word == "wont":
        return "will not"
    if word == "cant":
        return "cannot"
    if word == "isnt":
        return "is not"
    if word == "doesnt":
        return "does not"
    
    # Check if word needs correction
    suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
    if suggestions and suggestions[0].distance <= 2:
        return suggestions[0].term
    return word

def preprocess_user_query(query):
    """
    Preprocess user query by:
    1. Normalizing spacing and formatting
    2. Correcting spelling mistakes (preserving marine terms)
    3. Expanding common abbreviations
    4. Removing excessive stopwords
    5. Lemmatizing words
    """
    # Step 1: Normalize spacing and formatting
    # Convert to lowercase
    text = query.lower()
    
    # Fix unit formatting (e.g. "10bar" -> "10 bar")
    text = unit_pattern.sub(r'\1 \2', text)
    text = range_pattern.sub(r'\1-\2 \3', text)
    
    # Normalize spacing
    text = re.sub(r'\s+', ' ', text)
    
    # Standardize common variations
    text = text.replace("can't", "cannot")
    text = text.replace("won't", "will not")
    text = text.replace("isn't", "is not")
    
    # Step 2: Tokenize the text
    tokens = word_tokenize(text)
    
    # Step 3: Spell check individual words
    corrected_tokens = [spell_correct_word(token) for token in tokens]
    
    # Step 4: Expand abbreviations
    expanded_tokens = []
    for token in corrected_tokens:
        if token in abbreviations:
            expanded = abbreviations[token].split()
            expanded_tokens.extend(expanded)
        else:
            expanded_tokens.append(token)
    
    # Step 5: Remove stopwords (but preserve important ones)
    # Don't remove: not, no, nor, than, too, very, against, down, up, over, under
    important_stopwords = {'not', 'no', 'nor', 'than', 'too', 'very', 
                         'against', 'down', 'up', 'over', 'under', 'is', 'has', 'have', 'had'}
    stop_words = set(stopwords.words('english')) - important_stopwords
    filtered_tokens = [token for token in expanded_tokens if token not in stop_words or token in important_stopwords]
    
    # Step 6: Lemmatize words (convert to base form)
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in filtered_tokens]
    
    # Step 7: Reconstruct the query
    processed_query = ' '.join(lemmatized_tokens)
    
    # Step 8: Handle negations properly
    processed_query = processed_query.replace("not ", "not_")
    processed_query = processed_query.replace("no ", "no_")
    processed_query = processed_query.replace("n't ", "not_")
    
    return processed_query, text  # Return both processed query and normalized original

def add_missing_context(query, processed_query):
    """
    Add contextual information that might be missing in the query
    """
    enhanced_query = processed_query
    
    # Check if the query mentions a component without specifying engine type
    component_terms = ['temperature', 'pressure', 'vibration', 'leak', 'noise', 'alarm']
    engine_terms = ['engine', 'main', 'auxiliary', 'aux', 'generator', 'gen']
    
    has_component = any(term in processed_query for term in component_terms)
    has_engine = any(term in processed_query for term in engine_terms)
    
    # If query mentions a component but not an engine, assume main engine
    if has_component and not has_engine:
        enhanced_query = "main engine " + enhanced_query
    
    return enhanced_query

def extract_entities(query):
    """
    Extract key entities that might be useful for diagnosis
    """
    entities = {
        'component': None,
        'symptom': None,
        'value': None,
        'unit': None
    }
    
    # Extract temperature values with units
    temp_pattern = re.compile(r'(\d+)(?:\s*)(degree|deg|celsius|c|fahrenheit|f)')
    temp_match = temp_pattern.search(query.lower())
    if temp_match:
        entities['value'] = temp_match.group(1)
        entities['unit'] = temp_match.group(2)
    
    # Extract pressure values with units
    pressure_pattern = re.compile(r'(\d+)(?:\s*)(bar|psi|kpa|mpa)')
    pressure_match = pressure_pattern.search(query.lower())
    if pressure_match:
        entities['value'] = pressure_match.group(1)
        entities['unit'] = pressure_match.group(2)
    
    # Extract common components
    component_patterns = [
        (r'(main|auxiliary|aux)?\s*engine', 'engine'),
        (r'turbocharger', 'turbocharger'),
        (r'(fuel|lube|lubricating|cooling)\s*pump', 'pump'),
        (r'(cylinder|piston|liner|bearing|valve)', r'\1'),
        (r'(jacket|cooling)\s*water', 'cooling water'),
        (r'(air|exhaust)\s*filter', 'filter')
    ]
    
    for pattern, component_type in component_patterns:
        match = re.search(pattern, query.lower())
        if match:
            entities['component'] = component_type
            break
    
    # Extract symptoms
    symptom_patterns = [
        (r'(high|low|excessive)\s*(temperature|pressure|vibration|noise)', r'\1 \2'),
        (r'(leak|leaking|leakage)', 'leak'),
        (r'(overheat|overheating)', 'overheating'),
        (r'(not\s*start|won\'t\s*start|fails\s*to\s*start)', 'not starting'),
        (r'(alarm|warning)', 'alarm'),
        (r'(smoke|smoking)', 'smoke')
    ]
    
    for pattern, symptom_type in symptom_patterns:
        match = re.search(pattern, query.lower())
        if match:
            entities['symptom'] = symptom_type
            break
    
    return entities

def process_query(user_query):
    """
    Main function to process user queries
    """
    # Preprocess the query
    processed_query, normalized_query = preprocess_user_query(user_query)
    
    # Add missing context if needed
    enhanced_query = add_missing_context(user_query, processed_query)
    
    # Extract entities
    entities = extract_entities(user_query)
    
    return {
        'original_query': user_query,
        'normalized_query': normalized_query,
        'processed_query': processed_query,
        'enhanced_query': enhanced_query,
        'entities': entities
    }

# Example usage
if __name__ == "__main__":
    test_queries = [
        "Main engine temp is too high",
        "aux engine wont start when i press button",
        "theres a lot of vibration comming from the fuel oil purifyer",
        "engine temperature reached 95c",
        "turbocharger making wierd noise",
        "temp alarm on cylinder 3",
        "cooling water press dropped to 1.5bar",
        "there is smoke coming from exhoust"
    ]
    
    for query in test_queries:
        result = process_query(query)
        print(f"Original: {result['original_query']}")
        print(f"Processed: {result['processed_query']}")
        print(f"Enhanced: {result['enhanced_query']}")
        print(f"Entities: {result['entities']}")
        print("-" * 50)