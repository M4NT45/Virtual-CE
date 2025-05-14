from utils.yaml_parser import YamlReader
from models.DB_class import session_maker

class RuleEngine:
    def __init__(self):
        self.session_maker = session_maker
        
    def process(self, query):
        with self.session_maker() as session:
            yaml_reader = YamlReader(session)
            query_lower = query.lower()
            query_words = set(query_lower.split())
            all_faults = yaml_reader.get_all_faults()
            results = []
                        
            for fault in all_faults:
                if 'fault' not in fault:
                    continue
                    
                score = self._calculate_match_score(query_lower, query_words, fault)
                
                if score > 0:
                    results.append({
                        'fault': fault['fault']['name'],
                        'confidence': score,
                        'source_file': fault.get('_source_file', 'unknown'),
                        'fault_number': fault.get('_fault_number', 0),
                        'causes': fault['fault'].get('causes', []),
                        'source': 'rule_engine'
                    })
                    
            results.sort(key=lambda x: x['confidence'], reverse=True)
            return results
    
    def _calculate_match_score(self, query_lower, query_words, fault):
        # Extract fault information
        fault_name = fault['fault'].get('name', '').lower()
        symptoms = fault['fault'].get('symptoms', [])
        
        # Initialize scores
        exact_match_score = 0
        partial_match_score = 0
        name_match_score = 0
        
        # 1. Check for exact symptom matches
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            
            # Exact match of the full query
            if query_lower == symptom_lower:
                exact_match_score = 10.0
                break
                
            # Query is contained within the symptom
            if query_lower in symptom_lower:
                exact_match_score = max(exact_match_score, 5.0)
                
            # Calculate word match score
            symptom_words = set(symptom_lower.split())
            matching_words = query_words.intersection(symptom_words)
            
            if matching_words:
                # Calculate what percentage of query words match
                query_coverage = len(matching_words) / len(query_words)
                # Higher score if most of the query is covered
                if query_coverage > 0.7:
                    partial_match_score += 3.0 * query_coverage
                else:
                    partial_match_score += query_coverage
        
        # 2. Fault name matching
        fault_name_words = set(fault_name.split())
        matching_name_words = query_words.intersection(fault_name_words)
        if matching_name_words:
            name_match_score = 2.0 * len(matching_name_words) / len(query_words)
            
        # 3. Key terms scoring
        key_terms_score = 0
        key_terms = {
            "lubricating": 2.0, "oil": 1.0, "pressure": 1.0, 
            "crankcase": 2.0, "high": 0.5, "low": 0.5, 
            "alarm": 0.5, "hydraulic": 2.0
        }
        
        for term, weight in key_terms.items():
            if term in query_lower and term in fault_name:
                key_terms_score += weight
                
        # Combine all scores
        total_score = exact_match_score + partial_match_score + name_match_score + key_terms_score
        
        return total_score