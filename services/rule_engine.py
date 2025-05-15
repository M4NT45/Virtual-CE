from utils.yaml_parser import YamlReader
from models.DB_class import session_maker

class RuleEngine:
    def __init__(self):
        self.session_maker = session_maker

        # Term-to-file mappings
        self.file_mappings = {
            'temperature': ['temperatures.yaml'],
            'hot': ['temperatures.yaml'],
            'cold': ['temperatures.yaml'],
            'overheat': ['temperatures.yaml'],
            'heat': ['temperatures.yaml'],
            'thermal': ['temperatures.yaml'],
            'cooling': ['temperatures.yaml'],
            
            'pressure': ['pressures.yaml'],
            'high pressure': ['pressures.yaml'],
            'low pressure': ['pressures.yaml'],
            'bar': ['pressures.yaml'],
            'psi': ['pressures.yaml'],
            'kpa': ['pressures.yaml'],
            'vacuum': ['pressures.yaml'],

            'vibration': ['other.yaml'],
            'noise': ['other.yaml'],
            'knock': ['other.yaml'],
            'start': ['other.yaml'],
            'stop': ['other.yaml'],
            'rpm': ['other.yaml'],
            'speed': ['other.yaml'],
            'smoke': ['other.yaml'],
            'black': ['other.yaml'],
            'white': ['other.yaml'],
            'blue': ['other.yaml'],
            'gray': ['other.yaml'],
            'leak': ['other.yaml'],
            'exhaust': ['other.yaml'],
            'shutdown': ['other.yaml'],
            'emergency': ['other.yaml']
        }
        
        # Symptom categories and important terms
        self.symptom_categories = {
            'smoke': ['smoke', 'black', 'white', 'blue', 'gray', 'exhaust', 'emission', 'dark'],
            'temperature': ['temperature', 'hot', 'overheat', 'heat', 'cooling', 'cold'],
            'pressure': ['pressure', 'bar', 'psi', 'kpa', 'high', 'low'],
            'noise': ['noise', 'knock', 'vibration', 'sound', 'loud'],
            'operation': ['start', 'stop', 'run', 'operate', 'shutdown', 'trip'],
            'leakage': ['leak', 'drip', 'spill', 'escape']
        }
        
        # Important terms that should increase relevance when matching
        self.important_terms = {
            'black smoke': 10,
            'white smoke': 10,
            'blue smoke': 10,
            'gray smoke': 10,
            'smoke': 8,
            'exhaust gas': 7,
            'temperature high': 9,
            'high temperature': 9,
            'overheat': 9,
            'pressure low': 9,
            'low pressure': 9,
            'no pressure': 10,
            'knocking': 9,
            'won\'t start': 10,
            'will not start': 10,
            'fails to start': 10,
            'stops': 8,
            'shutdown': 8,
            'emergency': 9,
            'leaking': 8,
            'water in oil': 10,
            'oil in water': 10
        }

    def process(self, query, processed_data=None):
        print("=== RULE ENGINE DEBUG ===")
        print(f"Query: {query}")
        if processed_data:
            print(f"Processed data available with keys: {processed_data.keys()}")
        else:
            print("No processed data available")

        # Get query text - prioritize enhanced query if available
        if processed_data and processed_data.get('enhanced_query'):
            query_text = processed_data.get('enhanced_query')
            print(f"Using enhanced query: {query_text}")
        elif processed_data and processed_data.get('normalized_query'):
            query_text = processed_data.get('normalized_query')
            print(f"Using normalized query: {query_text}")
        else:
            query_text = query
            print(f"Using original query: {query_text}")

        query_lower = query_text.lower()
        query_words = set(query_lower.split())

        # Determine subsystem from multiple sources
        subsystem = None
        
        # 1. Try clarified_engine
        if processed_data and processed_data.get('clarified_engine'):
            engine_type = processed_data.get('clarified_engine')
            print(f"Found clarified_engine: {engine_type}")
            if 'main' in engine_type.lower():
                subsystem = 'main_engine'
            elif 'auxiliary' in engine_type.lower() or 'aux' in engine_type.lower():
                subsystem = 'auxiliary_engines'
            print(f"Subsystem from clarified_engine: {subsystem}")
        
        # 2. If no subsystem yet, try enhanced_query
        if not subsystem and processed_data and processed_data.get('enhanced_query'):
            enhanced_query = processed_data.get('enhanced_query').lower()
            print(f"Checking enhanced query: {enhanced_query}")
            if 'main engine' in enhanced_query:
                subsystem = 'main_engine'
                print(f"Found 'main engine' in enhanced query")
            elif 'auxiliary engine' in enhanced_query or 'aux engine' in enhanced_query:
                subsystem = 'auxiliary_engines'
                print(f"Found 'auxiliary engine' in enhanced query")
        
        # 3. If still no subsystem, check original query
        if not subsystem:
            if 'main engine' in query_lower or 'main' in query_lower:
                subsystem = 'main_engine'
                print(f"Defaulted to main_engine based on query")
            elif 'auxiliary engine' in query_lower or 'aux engine' in query_lower or 'auxiliary' in query_lower or 'aux' in query_lower:
                subsystem = 'auxiliary_engines'
                print(f"Defaulted to auxiliary_engines based on query")
        
        print(f"Final subsystem determination: {subsystem}")

        # Identify the main symptom category for the query
        query_categories = self._identify_symptom_categories(query_lower)
        print(f"Query symptom categories: {query_categories}")

        # Get file filters
        file_filters = self._get_relevant_files(query_lower)
        print(f"Using file filters: {file_filters}")

        # Get faults
        with self.session_maker() as session:
            yaml_reader = YamlReader(session)
            all_faults = yaml_reader.get_all_faults(subsystem=subsystem, file_filters=file_filters)
        
        print(f"Found {len(all_faults)} faults to process")
        
        # Process faults
        results = []
        for fault in all_faults:
            if 'fault' not in fault:
                continue
                
            confidence = self._calculate_overlap(query_lower, query_words, fault, query_categories)
            
            if confidence > 0:
                results.append({
                    'fault': fault['fault']['name'],
                    'confidence': confidence,
                    'source_file': fault.get('_source_file', 'unknown'),
                    'fault_number': fault.get('_fault_number', 0),
                    'causes': fault['fault'].get('causes', []),
                    'source': 'rule_engine',
                    'subsystem': fault.get('_subsystem', 'unknown')
                })

        results.sort(key=lambda x: x['confidence'], reverse=True)
        print(f"Returning {len(results)} matches")
        if results:
            print(f"Top match: {results[0]['fault']} (confidence: {results[0]['confidence']})")
        
        return results

    def _get_relevant_files(self, query):
        relevant_files = set()

        for term, files in self.file_mappings.items():
            if term in query:
                for file in files:
                    relevant_files.add(file)

        if not relevant_files:
            relevant_files = {'temperatures.yaml', 'pressures.yaml', 'other.yaml'}
            
        return list(relevant_files)
    
    def _identify_symptom_categories(self, query):
        """Identify which symptom categories the query belongs to"""
        categories = []
        
        for category, terms in self.symptom_categories.items():
            if any(term in query for term in terms):
                categories.append(category)
                
        return categories

    def _calculate_overlap(self, query_lower, query_words, fault, query_categories):
        fault_name = fault['fault'].get('name', '').lower()
        symptoms = [s.lower() for s in fault['fault'].get('symptoms', [])]
        
        # Get fault categories
        fault_categories = []
        combined_fault_text = fault_name + " " + " ".join(symptoms)
        for category, terms in self.symptom_categories.items():
            if any(term in combined_fault_text for term in terms):
                fault_categories.append(category)

        # Start with baseline confidence
        confidence = 0
        
        # 1. Check for important terms
        for term, boost in self.important_terms.items():
            if term in query_lower and term in combined_fault_text:
                confidence += boost
                print(f"Important term match: '{term}' - +{boost}")
        
        # 2. Category match bonus - prioritize faults that match the query category
        category_match = False
        for category in query_categories:
            if category in fault_categories:
                confidence += 5
                category_match = True
                print(f"Category match: '{category}' - +5")
        
        # 3. Direct name match
        if query_lower in fault_name:
            confidence += 8
            print(f"Query contained in fault name - +8")
        elif fault_name in query_lower:
            confidence += 6
            print(f"Fault name contained in query - +6")

        # 4. Word overlap in fault name
        fault_name_words = set(fault_name.split())
        name_overlap = query_words.intersection(fault_name_words)
        if name_overlap:
            overlap_ratio = len(name_overlap) / max(len(query_words), len(fault_name_words))
            word_score = 4 * overlap_ratio
            confidence += word_score
            print(f"Word overlap in name ({len(name_overlap)} words) - +{word_score:.2f}")

        # 5. Symptom matches
        symptom_match = False
        for symptom in symptoms:
            # Direct containment
            if query_lower in symptom:
                confidence += 7
                symptom_match = True
                print(f"Query found in symptom: '{symptom[:30]}...' - +7")
                break
            elif symptom in query_lower:
                confidence += 5
                symptom_match = True
                print(f"Symptom found in query: '{symptom[:30]}...' - +5")
                break

            # Word overlap with symptoms
            symptom_words = set(symptom.split())
            symptom_overlap = query_words.intersection(symptom_words)
            if symptom_overlap and len(symptom_overlap) >= 2:  # At least 2 matching words
                symptom_ratio = len(symptom_overlap) / max(len(query_words), len(symptom_words))
                symptom_score = 3 * symptom_ratio
                confidence += symptom_score
                symptom_match = True
                print(f"Word overlap in symptom ({len(symptom_overlap)} words) - +{symptom_score:.2f}")
        
        # If no category or symptom match, drastically reduce confidence
        if not category_match and not symptom_match and confidence < 8:
            confidence *= 0.3
            print(f"No category or symptom match - confidence reduced by 70%")
        
        # Round to make confidence values more readable
        return round(confidence, 2)