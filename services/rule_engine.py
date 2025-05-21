from utils.yaml_parser import YamlReader
from models.DB_class import session_maker

class RuleEngine:
    def __init__(self):
        self.session_maker = session_maker

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
        
        self.symptom_categories = {
            'smoke': ['smoke', 'black', 'white', 'blue', 'gray', 'exhaust', 'emission', 'dark'],
            'temperature': ['temperature', 'hot', 'overheat', 'heat', 'cooling', 'cold'],
            'pressure': ['pressure', 'bar', 'psi', 'kpa', 'high', 'low'],
            'noise': ['noise', 'knock', 'vibration', 'sound', 'loud'],
            'operation': ['start', 'stop', 'run', 'operate', 'shutdown', 'trip'],
            'leakage': ['leak', 'drip', 'spill', 'escape']
        }
        
        self.important_terms = {
            'high temperature': 12,
            'elevated temperature': 12,
            'temperature high': 12,
            'too hot': 12,
            'overheating': 12,
            'above normal': 12,
            'overheat': 9,
            
            'low temperature': 12,
            'temperature low': 12,
            'cold': 12,
            'below normal': 12,
            
            'high pressure': 12,
            'pressure high': 12,
            'above normal pressure': 12,
            
            'low pressure': 12,
            'pressure low': 12,
            'pressure lacking': 12,
            'no pressure': 15,
            'insufficient pressure': 12,
            'pressure drop': 12,
            
            'one cylinder high': 15,
            'single cylinder high': 15,
            'one cylinder above': 15,
            'single cylinder above': 15,
            'one cylinder below': 15,
            'single cylinder below': 15,
            'individual cylinder': 12,
            
            'black smoke': 10,
            'white smoke': 10,
            'blue smoke': 10,
            'gray smoke': 10,
            'smoke': 8,
            'exhaust gas': 7,
            
            'won\'t start': 10,
            'will not start': 10,
            'fails to start': 10,
            'stops': 8,
            'shutdown': 8,
            'emergency': 9,
            'knocking': 9,
            
            'water in oil': 10,
            'oil in water': 10,
            'leaking': 8
        }

    def process(self, query, processed_data=None):
        if processed_data and processed_data.get('enhanced_query'):
            query_text = processed_data.get('enhanced_query')
        elif processed_data and processed_data.get('normalized_query'):
            query_text = processed_data.get('normalized_query')
        else:
            query_text = query

        query_lower = query_text.lower()
        query_words = set(query_lower.split())

        subsystem = None
        
        if processed_data and processed_data.get('clarified_engine'):
            engine_type = processed_data.get('clarified_engine')
            if 'main' in engine_type.lower():
                subsystem = 'main_engine'
            elif 'auxiliary' in engine_type.lower() or 'aux' in engine_type.lower():
                subsystem = 'auxiliary_engines'
        
        if not subsystem and processed_data and processed_data.get('enhanced_query'):
            enhanced_query = processed_data.get('enhanced_query').lower()
            if 'main engine' in enhanced_query:
                subsystem = 'main_engine'
            elif 'auxiliary engine' in enhanced_query or 'aux engine' in enhanced_query:
                subsystem = 'auxiliary_engines'
        
        if not subsystem:
            if 'main engine' in query_lower or 'main' in query_lower:
                subsystem = 'main_engine'
            elif 'auxiliary engine' in query_lower or 'aux engine' in query_lower or 'auxiliary' in query_lower or 'aux' in query_lower:
                subsystem = 'auxiliary_engines'

        query_categories = self._identify_symptom_categories(query_lower)
        file_filters = self._get_relevant_files(query_lower)

        with self.session_maker() as session:
            yaml_reader = YamlReader(session)
            all_faults = yaml_reader.get_all_faults(subsystem=subsystem, file_filters=file_filters)
        
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
        categories = []
        
        for category, terms in self.symptom_categories.items():
            if any(term in query for term in terms):
                categories.append(category)
                
        return categories

    def _calculate_overlap(self, query_lower, query_words, fault, query_categories):
        fault_name = fault['fault'].get('name', '').lower()
        symptoms = [s.lower() for s in fault['fault'].get('symptoms', [])]
        
        directional_mismatch = self._check_directional_mismatch(query_lower, fault_name)
        specificity_mismatch = self._check_specificity_mismatch(query_lower, fault_name)
        
        if directional_mismatch:
            return 0.1

        fault_categories = []
        combined_fault_text = fault_name + " " + " ".join(symptoms)
        for category, terms in self.symptom_categories.items():
            if any(term in combined_fault_text for term in terms):
                fault_categories.append(category)

        confidence = 0
        
        for term, boost in self.important_terms.items():
            if term in query_lower and term in combined_fault_text:
                confidence += boost
        
        category_match = False
        for category in query_categories:
            if category in fault_categories:
                confidence += 5
                category_match = True
        
        if query_lower in fault_name:
            confidence += 8
        elif fault_name in query_lower:
            confidence += 6

        fault_name_words = set(fault_name.split())
        name_overlap = query_words.intersection(fault_name_words)
        if name_overlap:
            overlap_ratio = len(name_overlap) / max(len(query_words), len(fault_name_words))
            word_score = 4 * overlap_ratio
            confidence += word_score

        symptom_match = False
        for symptom in symptoms:
            if query_lower in symptom:
                confidence += 7
                symptom_match = True
                break
            elif symptom in query_lower:
                confidence += 5
                symptom_match = True
                break

            symptom_words = set(symptom.split())
            symptom_overlap = query_words.intersection(symptom_words)
            if symptom_overlap and len(symptom_overlap) >= 2:
                symptom_ratio = len(symptom_overlap) / max(len(query_words), len(symptom_words))
                symptom_score = 3 * symptom_ratio
                confidence += symptom_score
                symptom_match = True
        
        if specificity_mismatch:
            confidence *= 0.5
        
        if not category_match and not symptom_match and confidence < 8:
            confidence *= 0.3
        
        return round(confidence, 2)
    
    def _check_directional_mismatch(self, query_lower, fault_name):
        query_high_indicators = ['high', 'above', 'elevated', 'too hot', 'hot', 'increase', 'rise']
        query_low_indicators = ['low', 'below', 'cold', 'lacking', 'decrease', 'drop', 'insufficient']
        
        fault_high_indicators = ['high', 'above', 'elevated', 'increase', 'rise']
        fault_low_indicators = ['low', 'below', 'lacking', 'decrease', 'drop', 'insufficient']
        
        query_has_high = any(term in query_lower for term in query_high_indicators)
        query_has_low = any(term in query_lower for term in query_low_indicators)
        fault_has_high = any(term in fault_name for term in fault_high_indicators)
        fault_has_low = any(term in fault_name for term in fault_low_indicators)
        
        mismatch = ((query_has_high and fault_has_low) or 
                   (query_has_low and fault_has_high))
        
        return mismatch
    
    def _check_specificity_mismatch(self, query_lower, fault_name):
        query_specific_indicators = ['one', 'single', 'individual', 'specific']
        query_general_indicators = ['all', 'every', 'multiple', 'general']
        
        fault_specific_indicators = ['one', 'single', 'individual']
        fault_general_indicators = ['all', 'every', 'multiple']
        
        if 'cylinder' not in query_lower and 'cylinder' not in fault_name:
            return False
        
        query_has_specific = any(term in query_lower for term in query_specific_indicators)
        query_has_general = any(term in query_lower for term in query_general_indicators)
        fault_has_specific = any(term in fault_name for term in fault_specific_indicators)
        fault_has_general = any(term in fault_name for term in fault_general_indicators)
        
        mismatch = ((query_has_specific and fault_has_general) or 
                   (query_has_general and fault_has_specific))
        
        return mismatch