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
    """
    Analyze query and determine if clarification is needed for engine, component, or problem type.
    Returns enhanced query or clarification request.
    """
    
    ENGINE_TERMS = ['main', 'auxiliary', 'aux', 'generator', 'gen', 'me', 'ae', 'dg']
    
    COMPONENT_TERMS = ['temperature', 'pressure', 'vibration', 'smoke', 'noise', 
                       'cooling', 'fuel', 'oil', 'turbocharger', 'exhaust', 'bearing']
    
    PROBLEM_TERMS = ['high', 'low', 'excessive', 'insufficient', 'abnormal', 'unusual',
                     'leak', 'leaking', 'hot', 'cold', 'loud', 'rough', 'black', 'white', 'blue']
    
    ACTION_TERMS = ['start', 'starting', 'stop', 'stopping', 'run', 'running', 'work', 'working']
    
    VAGUE_TERMS = ['problem', 'issue', 'trouble', 'fault', 'wrong', 'bad', 'strange', 
                   'something', 'it', 'that', 'not good', 'acting up', 'broken', 'damaged',
                   'kaput', 'failed', 'failure', 'dead', 'gone', 'finished', 'malfunctioning']
    
    def get_engine_type(text):
        text_lower = text.lower()
        if 'main' in text_lower or 'me' in text_lower:
            return "main engine"
        elif any(term in text_lower for term in ['auxiliary', 'aux', 'ae', 'generator', 'gen', 'dg']):
            return "auxiliary engine"
        elif 'engine' in text_lower:
            return "unspecified"
        return None
    
    def analyze_query(text):
        text_lower = text.lower()
        return {
            'has_engine': any(term in text_lower for term in ENGINE_TERMS),
            'has_component': any(term in text_lower for term in COMPONENT_TERMS),
            'has_problem': any(term in text_lower for term in PROBLEM_TERMS),
            'has_action': any(term in text_lower for term in ACTION_TERMS),
            'is_vague': any(term in text_lower for term in VAGUE_TERMS),
            'engine_type': get_engine_type(text)
        }
    
    if conversation_state and conversation_state.get('awaiting_clarification'):
        
        if conversation_state['awaiting_clarification'] == 'engine':
            engine_type = get_engine_type(processed_query) or "main engine" 
            original_query = conversation_state.get('original_query', '')
            
            original_analysis = analyze_query(original_query)
            
            if original_analysis['is_vague'] or (not original_analysis['has_component'] and not original_analysis['has_problem']):
                return {
                    "enhanced_query": None,
                    "needs_clarification": True,
                    "awaiting_clarification": "component",
                    "clarification_message": f"What specific issue are you experiencing with the {engine_type}?",
                    "original_query": original_query,
                    "clarified_engine": engine_type
                }
            else:
                return {
                    "enhanced_query": f"{engine_type} {original_query}",
                    "needs_clarification": False,
                    "awaiting_clarification": None
                }
        
        elif conversation_state['awaiting_clarification'] == 'component':
            clarified_engine = conversation_state.get('clarified_engine', 'engine')
            original_query = conversation_state.get('original_query', '')
            
            component_info = processed_query
            
            if analyze_query(component_info)['is_vague'] and not analyze_query(component_info)['has_component']:
                # Ask for more specific info
                return {
                    "enhanced_query": None,
                    "needs_clarification": True,
                    "awaiting_clarification": "problem",
                    "clarification_message": "Please be more specific. Is it related to temperature, pressure, noise, starting issues, or something else?",
                    "original_query": original_query,
                    "clarified_engine": clarified_engine,
                    "clarified_component": component_info
                }
            else:
                # Construct final query
                return {
                    "enhanced_query": f"{clarified_engine} {component_info}",
                    "needs_clarification": False,
                    "awaiting_clarification": None
                }
        
        elif conversation_state['awaiting_clarification'] == 'problem':
            clarified_engine = conversation_state.get('clarified_engine', 'engine')
            clarified_component = conversation_state.get('clarified_component', '')

            return {
                "enhanced_query": f"{clarified_engine} {clarified_component} {processed_query}",
                "needs_clarification": False,
                "awaiting_clarification": None
            }
    
    analysis = analyze_query(processed_query)
    
    if analysis['is_vague'] and not analysis['has_engine'] and not analysis['has_component']:
        return {
            "enhanced_query": None,
            "needs_clarification": True,
            "awaiting_clarification": "engine",
            "clarification_message": "I need more information. Which engine are you referring to?",
            "original_query": processed_query
        }
    
    elif analysis['engine_type'] == "unspecified":
        return {
            "enhanced_query": None,
            "needs_clarification": True,
            "awaiting_clarification": "engine",
            "clarification_message": "Which engine are you referring to? (Main Engine or Auxiliary Engine)",
            "original_query": processed_query
        }
    
    elif (analysis['has_component'] or analysis['has_problem'] or analysis['has_action']) and not analysis['has_engine']:
        return {
            "enhanced_query": None,
            "needs_clarification": True,
            "awaiting_clarification": "engine",
            "clarification_message": "Which engine are you referring to? (Main Engine or Auxiliary Engine)",
            "original_query": processed_query
        }
    
    elif analysis['has_engine'] and analysis['is_vague'] and not analysis['has_component'] and not analysis['has_problem']:
        return {
            "enhanced_query": None,
            "needs_clarification": True,
            "awaiting_clarification": "component",
            "clarification_message": f"What specific issue are you experiencing with the {analysis['engine_type']}?",
            "original_query": processed_query,
            "clarified_engine": analysis['engine_type']
        }
    
    elif analysis['has_engine'] and analysis['has_action'] and not analysis['has_problem']:
        return {
            "enhanced_query": processed_query,
            "needs_clarification": False,
            "awaiting_clarification": None
        }
    
    else:
        return {
            "enhanced_query": processed_query,
            "needs_clarification": False,
            "awaiting_clarification": None
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