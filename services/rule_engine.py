from utils.yaml_parser import YamlReader

class RuleEngine:
    def __init__(self):
        self.yaml_reader = YamlReader()
    
    def process(self, query):
        # For MVP: simple keyword matching
        query_words = set(query.lower().split())
        all_faults = self.yaml_reader.get_all_faults()
        
        results = []
        for fault in all_faults:
            score = self._calculate_match_score(query_words, fault)
            if score > 0:
                results.append({
                    'fault': fault['fault']['name'],
                    'confidence': score,
                    'causes': fault['fault']['causes'],
                    'source': 'rule_engine'
                })
        
        # Sort by confidence score
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results
    
    def _calculate_match_score(self, query_words, fault):
        # Extract all symptoms
        symptoms = fault['fault']['symptoms']
        symptom_words = set()
        for symptom in symptoms:
            symptom_words.update(symptom.lower().split())
        
        # Count matching words
        matches = query_words.intersection(symptom_words)
        
        # Simple score: proportion of matching words
        if len(symptom_words) > 0:
            return len(matches) / len(symptom_words)
        return 0