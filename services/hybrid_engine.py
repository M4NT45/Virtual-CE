from services.rule_engine import RuleEngine
from services.neural_engine import NeuralEngine

class HybridEngine:
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.neural_engine = NeuralEngine()
    
    def process(self, query, processed_data=None):
        try:
            rule_results = self.rule_engine.process(query, processed_data=processed_data)
        except Exception as e:
            rule_results = []
        
        try:
            neural_results = self.neural_engine.process(query, processed_data=processed_data)
        except Exception as e:
            neural_results = []
        
        unknown_detection = self._detect_unknown_query(query, rule_results, neural_results)
        
        if unknown_detection['is_unknown']:
            penalty = unknown_detection['confidence_penalty']
            for result in rule_results:
                result['confidence'] *= penalty
            for result in neural_results:
                result['confidence'] *= penalty
        
        combined_results = self._combine_results(rule_results, neural_results)
        
        if unknown_detection['is_unknown']:
            return {
                'results': combined_results,
                'is_unknown_query': True,
                'unknown_message': unknown_detection['message'],
                'missing_terms': unknown_detection['missing_terms'],
                'suggestion': "Try rephrasing your query or check if the equipment/system is covered in the fault database."
            }
        
        return combined_results
    
    def _detect_unknown_query(self, query, rule_results, neural_results):
        query_lower = query.lower()
        key_terms = []
        
        specific_equipment = [
            'seawater', 'sea water', 'raw water', 'ballast', 'bilge', 'freshwater', 'potable water',
            'stern tube', 'propeller shaft', 'rudder', 'thruster', 'bow thruster', 'azimuth',
            'winch', 'crane', 'windlass', 'mooring', 'anchor', 'davit', 'hatch', 'ramp',
            'radar', 'sonar', 'gps', 'compass', 'autopilot', 'gyro', 'ecdis', 'vhf', 'radio',
            'ventilation', 'hvac', 'air conditioning', 'galley', 'accommodation', 'cabin',
            'sewage', 'waste', 'incinerator', 'garbage', 'sanitary', 'black water', 'grey water',
            'deck', 'hull', 'superstructure', 'mast', 'bridge', 'engine room', 'workshop',
            'cargo hold', 'tank', 'void space', 'cofferdams',
            'hydraulic', 'pneumatic', 'oily water separator', 'ows', 'sewage treatment',
            'reverse osmosis', 'ro plant', 'fresh water generator', 'fwg',
            'fire', 'sprinkler', 'foam', 'co2', 'lifeboat', 'life raft', 'emergency',
            'alarm system', 'public address', 'pa system',
            'loading', 'unloading', 'cargo pump', 'manifold', 'pipeline'
        ]
        
        for term in specific_equipment:
            if term in query_lower:
                key_terms.append(term)
        
        non_engine_indicators = [
            'room', 'space', 'area', 'compartment', 'leak', 'leakage', 'flooding',
            'fire', 'smoke detector', 'safety', 'emergency', 'spill'
        ]
        
        general_indicators = []
        for indicator in non_engine_indicators:
            if indicator in query_lower and indicator not in ['alarm']:
                general_indicators.append(indicator)
        
        if key_terms or general_indicators:
            all_special_terms = key_terms + general_indicators
            total_checked = min(10, len(rule_results) + len(neural_results))
            
            if total_checked == 0:
                return {
                    'is_unknown': True,
                    'missing_terms': all_special_terms,
                    'confidence_penalty': 0.0,
                    'message': f"No faults found related to '{', '.join(all_special_terms)}'. This equipment/system may not be covered in the engine fault database."
                }
            
            relevant_results = 0
            for result in (rule_results + neural_results)[:total_checked]:
                fault_name = result['fault'].lower()
                fault_causes = []
                fault_symptoms = []
                
                if 'causes' in result:
                    fault_causes = [str(cause).lower() for cause in result['causes']]
                if 'symptoms' in result:
                    fault_symptoms = [str(symptom).lower() for symptom in result['symptoms']]
                
                all_fault_text = fault_name + ' ' + ' '.join(fault_causes) + ' ' + ' '.join(fault_symptoms)
                
                if any(term in all_fault_text for term in all_special_terms):
                    relevant_results += 1
            
            relevance_ratio = relevant_results / total_checked if total_checked > 0 else 0
            
            if relevance_ratio == 0.0:
                return {
                    'is_unknown': True,
                    'missing_terms': all_special_terms,
                    'confidence_penalty': 0.1,
                    'message': f"No engine faults found related to '{', '.join(all_special_terms)}'. The returned results are general engine issues that may not be relevant to your specific query."
                }
            elif relevance_ratio < 0.2:
                return {
                    'is_unknown': True,
                    'missing_terms': all_special_terms,
                    'confidence_penalty': 0.3,
                    'message': f"Limited engine fault information available for '{', '.join(all_special_terms)}'. Showing general engine faults that may be indirectly related."
                }
            elif relevance_ratio < 0.5:
                return {
                    'is_unknown': True,
                    'missing_terms': all_special_terms,
                    'confidence_penalty': 0.6,
                    'message': f"Some engine faults found related to '{', '.join(all_special_terms)}', but coverage may be limited."
                }
        
        all_results = rule_results + neural_results
        if all_results:
            normalized_confidences = []
            for result in all_results:
                if result.get('source') == 'rule_engine' or 'rule' in result.get('source', ''):
                    normalized_conf = min(1.0, result['confidence'] / 20.0)
                else:
                    normalized_conf = result['confidence']
                normalized_confidences.append(normalized_conf)
            
            avg_confidence = sum(normalized_confidences) / len(normalized_confidences)
            max_confidence = max(normalized_confidences)
            
            if avg_confidence < 0.25 and max_confidence < 0.4:
                return {
                    'is_unknown': True,
                    'missing_terms': [],
                    'confidence_penalty': 1.0,
                    'message': "Low confidence in all matches. Your query might be about equipment or issues not well covered in the engine fault database."
                }
        
        return {'is_unknown': False}
    
    def _combine_results(self, rule_results, neural_results):
        normalized_rule_results = []
        for result in rule_results:
            normalized_result = result.copy()
            normalized_confidence = min(1.0, result['confidence'] / 20.0)
            normalized_result['confidence'] = normalized_confidence
            normalized_result['source'] = 'rule_engine_hybrid'
            normalized_rule_results.append(normalized_result)
        
        normalized_neural_results = []
        for result in neural_results:
            normalized_result = result.copy()
            normalized_result['source'] = 'neural_engine_hybrid'
            normalized_neural_results.append(normalized_result)
        
        combined_dict = {}
        
        for result in normalized_rule_results:
            fault_name = result['fault']
            combined_dict[fault_name] = result
            
        for result in normalized_neural_results:
            fault_name = result['fault']
            
            if fault_name not in combined_dict:
                combined_dict[fault_name] = result
            else:
                existing = combined_dict[fault_name]
                
                if result['confidence'] > existing['confidence']:
                    boosted_confidence = min(1.0, result['confidence'] * 1.2)
                    result['confidence'] = boosted_confidence
                    result['source'] = 'both_engines'
                    combined_dict[fault_name] = result
                else:
                    boosted_confidence = min(1.0, existing['confidence'] * 1.2)
                    existing['confidence'] = boosted_confidence
                    existing['source'] = 'both_engines'
        
        combined_list = list(combined_dict.values())
        combined_list.sort(key=lambda x: x['confidence'], reverse=True)
        
        return combined_list[:5]
    