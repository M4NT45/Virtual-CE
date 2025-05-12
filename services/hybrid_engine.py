from services.rule_engine import RuleEngine
from services.neural_engine import NeuralEngine

class HybridEngine:
    def __init__(self):
        self.rule_engine = RuleEngine()
        self.neural_engine = NeuralEngine()
    
    def process(self, query):
        # First try rule-based approach
        rule_results = self.rule_engine.process(query)
        
        # If confident results found, return them
        if rule_results and rule_results[0]['confidence'] > 0.7:
            return rule_results
        
        # Otherwise, fall back to neural approach
        neural_results = self.neural_engine.process(query)
        
        # Combine and rank results
        combined_results = self._combine_results(rule_results, neural_results)
        
        return combined_results
    
    def _combine_results(self, rule_results, neural_results):
        # Start with a dictionary to track unique faults
        combined_dict = {}
        
        # Add rule results first
        for result in rule_results:
            fault_name = result['fault']
            if fault_name not in combined_dict:
                combined_dict[fault_name] = result
            else:
                # Keep highest confidence
                if result['confidence'] > combined_dict[fault_name]['confidence']:
                    combined_dict[fault_name] = result
        
        # Then neural results (will override rule results if higher confidence)
        for result in neural_results:
            fault_name = result['fault']
            if fault_name not in combined_dict:
                combined_dict[fault_name] = result
            else:
                # Apply a slight bias towards rule engine (more reliable)
                neural_confidence = result['confidence']
                rule_confidence = combined_dict[fault_name].get('confidence', 0)
                
                if neural_confidence > rule_confidence * 1.1:  # 10% threshold to override
                    combined_dict[fault_name] = result
        
        # Convert back to list and sort
        combined_list = list(combined_dict.values())
        combined_list.sort(key=lambda x: x['confidence'], reverse=True)
        
        return combined_list