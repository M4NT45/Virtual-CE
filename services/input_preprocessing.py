import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from symspellpy import SymSpell, Verbosity
import pkg_resources

lemmatizer = WordNetLemmatizer()

sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
dictionary_path = pkg_resources.resource_filename(
    "symspellpy", "frequency_dictionary_en_82_765.txt")

sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)

marine_terms = {
    'hfo', 'mdo', 'lshfo', 'lsfo', 'vlsfo', 'mgb', 'mcr', 'rpm', 'turbocharger', 
    'scavenge', 'purifier', 'aux', 'auxiliary', 'mgo', 'lub', 'lube', 'fo', 'lo', 
    'kw', 'kwh', 'mlb', 'ppm', 'tbn', 'tbnb', 'hvac', 'me', 'ae', 'dg', 'genset', 
    'hvac', 'lpg', 'lng', 'co2', 'nox', 'sox', 'psi', 'mpa', 'bar', 'kpa',
    'crankcase', 'scavenging', 'crosshead', 'turbine', 'compressor', 'propeller',
    'injector', 'boiler', 'economizer', 'evaporator', 'viscosity', 'classifier', 
    'cooler', 'intercooler', 'aftercooler'
}

manufacturer_terms = {
    'wartsila', 'man', 'sulzer', 'yanmar', 'caterpillar', 'cat', 'mak', 'bergen', 
    'rolls-royce', 'rolls', 'royce', 'mitsubishi', 'daihatsu', 'cummins', 'deutz', 
    'pielstick', 'abb', 'woodward', 'alfa', 'laval', 'alfalaval'
}

domain_terms = marine_terms.union(manufacturer_terms)

unit_pattern = re.compile(r'(\d+)([a-zA-Z]+)')
range_pattern = re.compile(r'(\d+)-(\d+)([a-zA-Z]+)')

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

for term in domain_terms:
    sym_spell.create_dictionary_entry(term, 1000)

for misspelled, correct in marine_corrections.items():
    sym_spell.create_dictionary_entry(correct, 1000)

def spell_correct_word(word):
    if (word in domain_terms or 
        len(word) <= 2 or 
        word.isdigit() or 
        any(char.isdigit() for char in word)):
        return word

    if word == "wont":
        return "will not"
    if word == "cant":
        return "cannot"
    if word == "isnt":
        return "is not"
    if word == "doesnt":
        return "does not"
    
    suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
    if suggestions and suggestions[0].distance <= 2:
        return suggestions[0].term
    return word

def preprocess_user_query(query):

    text = query.lower()

    text = unit_pattern.sub(r'\1 \2', text)
    text = range_pattern.sub(r'\1-\2 \3', text)

    text = re.sub(r'\s+', ' ', text)

    text = text.replace("can't", "cannot")
    text = text.replace("won't", "will not")
    text = text.replace("isn't", "is not")

    tokens = word_tokenize(text)

    corrected_tokens = [spell_correct_word(token) for token in tokens]

    expanded_tokens = []
    for token in corrected_tokens:
        if token in abbreviations:
            expanded = abbreviations[token].split()
            expanded_tokens.extend(expanded)
        else:
            expanded_tokens.append(token)
    
    important_stopwords = {'not', 'no', 'nor', 'than', 'too', 'very', 
                         'against', 'down', 'up', 'over', 'under', 'is', 'has', 'have', 'had'}
    stop_words = set(stopwords.words('english')) - important_stopwords
    
    filtered_tokens = [token for token in expanded_tokens if token not in stop_words]

    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in filtered_tokens]
    
    processed_query = ' '.join(lemmatized_tokens)

    processed_query = processed_query.replace("not ", "not_")
    processed_query = processed_query.replace("no ", "no_")
    processed_query = processed_query.replace("n't ", "not_")
    
    return processed_query, text

def add_missing_context(processed_query, conversation_state=None):

    component_terms = ['temperature', 'pressure', 'vibration', 'leak', 'noise', 'alarm', 
                      'smoke', 'start', 'power', 'speed', 'rpm', 'fuel', 'oil', 'water',
                      'coolant', 'exhaust', 'filter', 'pump', 'valve', 'injector', 'bearing',
                      'turbocharger', 'cooling', 'lubrication', 'electrical', 'ignition']
    
    engine_terms = ['main', 'auxiliary', 'aux', 'generator', 'gen']
    
    problem_indicators = ['wrong', 'issue', 'problem', 'fault', 'error', 'trouble', 'fail', 
                         'not work', 'broken', 'malfunction', 'not run', 'stop', 'high', 'low',
                         'bad', 'strange', 'unusual', 'excessive', 'insufficient', 'poor', 'stuck',
                         'leaking', 'overheating', 'running hot', 'won\'t start', 'stalls', 
                         'rough', 'noisy', 'vibrating', 'smoking', 'alarm', 'warning', 'emergency',
                         'shutdown', 'tripped', 'irregular', 'intermittent', 'erratic', 'damaged',
                         'worn', 'burning', 'smell', 'knocking', 'rattling', 'grinding', 'loud']
    
    has_component = any(term in processed_query for term in component_terms)
    has_engine = any(term in processed_query for term in engine_terms)
    has_problem = any(term in processed_query for term in problem_indicators)
    
    def extract_engine_type(query):
        if "main" in query:
            return "main engine"
        elif any(term in query for term in ['auxiliary', 'aux', 'generator', 'gen']):
            return "auxiliary engine"
        else:
            return "main engine" 

    if conversation_state and conversation_state.get('awaiting_clarification') == 'engine':
        
        engine_response = processed_query.lower()

        clarified_engine = extract_engine_type(engine_response)
        
        original_query = conversation_state.get('original_query', '')
        
        if has_problem or any(term in original_query for term in problem_indicators):
            if not has_component and not any(term in original_query for term in component_terms):
                return {
                    "enhanced_query": None,
                    "needs_clarification": True,
                    "awaiting_clarification": "component",
                    "clarification_message": f"What specific issue are you observing with the {clarified_engine}? (temperature, pressure, noise, not starting, etc.)",
                    "original_query": clarified_engine + " " + original_query,
                    "clarified_engine": clarified_engine
                }
        

        enhanced_query = clarified_engine + " " + original_query
        return {
            "enhanced_query": enhanced_query,
            "needs_clarification": False,
            "awaiting_clarification": None,
            "original_query": None
        }
    
    if conversation_state and conversation_state.get('awaiting_clarification') == 'component':
        component_response = processed_query.lower()
        clarified_engine = conversation_state.get('clarified_engine', 'engine')
        
        mentioned_components = []
        for component in component_terms:
            if component in component_response:
                mentioned_components.append(component)
        
        if mentioned_components:
            primary_component = mentioned_components[0]
            enhanced_query = clarified_engine + " " + primary_component + " issue"
            if len(mentioned_components) > 1:
                enhanced_query += " with " + " and ".join(mentioned_components[1:])
        else:
            if "not" in component_response or "won't" in component_response or "doesn't" in component_response:
                enhanced_query = clarified_engine + " not functioning properly"
            else:
                for indicator in problem_indicators:
                    if indicator in component_response:
                        enhanced_query = clarified_engine + " " + indicator + " issue"
                        break
                else:
                    enhanced_query = clarified_engine + " operational issue"
        
        return {
            "enhanced_query": enhanced_query,
            "needs_clarification": False,
            "awaiting_clarification": None,
            "original_query": None
        }
    
    if has_component and not has_engine:
        return {
            "enhanced_query": None,
            "needs_clarification": True,
            "awaiting_clarification": "engine",
            "clarification_message": "Which engine are you referring to? (Main Engine, Auxiliary Engine, Generator)",
            "original_query": processed_query
        }
    
    elif has_engine and has_problem and not has_component:
        engine_type = extract_engine_type(processed_query)
        
        return {
            "enhanced_query": None,
            "needs_clarification": True,
            "awaiting_clarification": "component",
            "clarification_message": f"What specific issue are you observing with the {engine_type}? (temperature, pressure, noise, not starting, etc.)",
            "original_query": processed_query,
            "clarified_engine": engine_type
        }
    
    else:
        return {
            "enhanced_query": processed_query,
            "needs_clarification": False,
            "awaiting_clarification": None,
            "original_query": None
        }

def process_query(user_query, conversation_state=None):

    processed_query, normalized_query = preprocess_user_query(user_query)
    context_result = add_missing_context(processed_query, conversation_state)
    
    return {
        'original_query': user_query,
        'normalized_query': normalized_query,
        'processed_query': processed_query,
        'enhanced_query': context_result.get("enhanced_query"),
        'needs_clarification': context_result.get("needs_clarification", False),
        'clarification_message': context_result.get("clarification_message"),
        'awaiting_clarification': context_result.get("awaiting_clarification"),
        'original_query_for_clarification': context_result.get("original_query"),
        'clarified_engine': context_result.get("clarified_engine")
    }