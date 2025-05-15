from utils.yaml_parser import YamlReader
from models.DB_class import session_maker

class RuleEngine:
    """
    A rule engine optimized for your specific knowledge base structure with
    subsystem folders and categorized YAML files.
    """
    def __init__(self):
        self.session_maker = session_maker
        
        # Map query topics to specific YAML files based on your folder structure
        self.file_mappings = {
            # Temperature-related terms map to temperatures.yaml
            'temperature': ['temperatures.yaml'],
            'hot': ['temperatures.yaml'],
            'cold': ['temperatures.yaml'],
            'overheat': ['temperatures.yaml'],
            'heat': ['temperatures.yaml'],
            'thermal': ['temperatures.yaml'],
            'cooling': ['temperatures.yaml'],
            
            # Pressure-related terms map to pressures.yaml
            'pressure': ['pressures.yaml'],
            'high pressure': ['pressures.yaml'],
            'low pressure': ['pressures.yaml'],
            'bar': ['pressures.yaml'],
            'psi': ['pressures.yaml'],
            'kpa': ['pressures.yaml'],
            'vacuum': ['pressures.yaml'],
            
            # Other general issues map to other.yaml
            'vibration': ['other.yaml'],
            'noise': ['other.yaml'],
            'knock': ['other.yaml'],
            'start': ['other.yaml'],
            'stop': ['other.yaml'],
            'rpm': ['other.yaml'],
            'speed': ['other.yaml'],
            'smoke': ['other.yaml'],
            'leak': ['other.yaml'],
            'exhaust': ['other.yaml'],
            'shutdown': ['other.yaml'],
            'emergency': ['other.yaml']
        }

    def process(self, query, processed_data=None):
        """
        Process user query by finding matching faults in the most relevant YAML files.
        """
        # Use preprocessed data if available, otherwise use raw query
        if processed_data and processed_data.get('normalized_query'):
            query_text = processed_data.get('normalized_query')
        else:
            query_text = query
            
        # Get query words for matching
        query_lower = query_text.lower()
        query_words = set(query_lower.split())
        
        # Determine engine subsystem from preprocessed data
        subsystem = None
        if processed_data:
            # Extract engine type from processed data if available
            if processed_data.get('clarified_engine'):
                engine_type = processed_data.get('clarified_engine')
                # Map the engine type to your folder structure
                if 'main' in engine_type.lower():
                    subsystem = 'main_engine'
                elif 'auxiliary' in engine_type.lower() or 'aux' in engine_type.lower():
                    subsystem = 'auxiliary_engines'
                # Add other mappings if needed
        
        # Determine which YAML files to check based on query content
        file_filters = self._get_relevant_files(query_lower)
        
        # Get faults only for the identified subsystem and matching file filters
        with self.session_maker() as session:
            yaml_reader = YamlReader(session)
            all_faults = yaml_reader.get_all_faults(subsystem=subsystem, file_filters=file_filters)
        
        # Find matches based on word overlap
        results = []
        for fault in all_faults:
            # Skip invalid fault entries
            if 'fault' not in fault:
                continue
                
            # Calculate match confidence
            confidence = self._calculate_overlap(query_lower, query_words, fault)
            
            # Add to results if there's a match
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
        
        # Sort results by confidence score (highest first)
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results

    def _get_relevant_files(self, query):
        """
        Determine which YAML files are relevant based on the query content.
        Maps directly to your file structure.
        """
        relevant_files = set()
        
        # Check for each mapping term in the query
        for term, files in self.file_mappings.items():
            if term in query:
                for file in files:
                    relevant_files.add(file)
        
        # If no specific files matched or general query, include all files
        if not relevant_files:
            relevant_files = {'temperatures.yaml', 'pressures.yaml', 'other.yaml'}
            
        return list(relevant_files)

    def _calculate_overlap(self, query_lower, query_words, fault):
        """
        Calculate the overlap between query and fault based on word matching.
        """
        # Extract fault information
        fault_name = fault['fault'].get('name', '').lower()
        symptoms = [s.lower() for s in fault['fault'].get('symptoms', [])]
        
        # Start with no confidence
        confidence = 0
        
        # Check for direct phrase containment in fault name (highest priority)
        if query_lower in fault_name:
            confidence += 10
        elif fault_name in query_lower:
            confidence += 8
            
        # Check for word overlap in fault name
        fault_name_words = set(fault_name.split())
        name_overlap = query_words.intersection(fault_name_words)
        if name_overlap:
            # Higher weight for proportionally more matching words
            overlap_ratio = len(name_overlap) / max(len(query_words), len(fault_name_words))
            confidence += 5 * overlap_ratio
            
        # Check symptoms for matches
        for symptom in symptoms:
            # Direct containment
            if query_lower in symptom:
                confidence += 4
                break
            elif symptom in query_lower:
                confidence += 3
                break
                
            # Word overlap with symptoms
            symptom_words = set(symptom.split())
            symptom_overlap = query_words.intersection(symptom_words)
            if symptom_overlap:
                # Calculate overlap ratio for this symptom
                symptom_ratio = len(symptom_overlap) / max(len(query_words), len(symptom_words))
                # Take the best matching symptom
                confidence = max(confidence, 2 * symptom_ratio)
                
        return confidence