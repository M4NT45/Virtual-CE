from utils.yaml_parser import YamlReader
from models.DB_class import session_maker

class RuleEngine:
    def __init__(self):
        self.session_maker = session_maker
    
    def process(self, query):
        with session_maker() as session:
            yaml_reader = YamlReader(session)
            query_words = set(query.lower().split())
            all_faults = yaml_reader.get_all_faults()
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
            
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results
    
    def _calculate_match_score(self, query_words, fault):
        symptoms = fault['fault']['symptoms']
        symptom_words = set()
        
        for symptom in symptoms:
            symptom_words.update(symptom.lower().split())
        
        matches = query_words.intersection(symptom_words)

        if len(symptom_words) > 0:
            return len(matches) / len(symptom_words)
        return 0