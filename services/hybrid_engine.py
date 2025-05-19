from services.rule_engine import RuleEngine
from services.neural_engine import NeuralEngine

class HybridEngine:
    def __init__(self):
        print("=== HYBRID ENGINE INITIALIZING ===")
        self.rule_engine = RuleEngine()
        self.neural_engine = NeuralEngine()
    
    def process(self, query, processed_data=None):
        """
        Hybrid processing that combines rule-based and neural approaches
        with unknown query detection
        
        Strategy:
        1. Always try rule engine first (fast, deterministic)
        2. Always try neural engine (semantic matching)
        3. Detect unknown queries (terms not in knowledge base)
        4. Combine results intelligently with confidence adjustments
        """
        
        print(f"🔄 Hybrid Engine Processing: '{query}'")
        
        # Try rule-based approach
        print("  → Running rule engine...")
        try:
            rule_results = self.rule_engine.process(query, processed_data=processed_data)
            print(f"  ✅ Rule engine found {len(rule_results)} results")
            if rule_results:
                print(f"     Best rule match: {rule_results[0]['fault']} (confidence: {rule_results[0]['confidence']})")
        except Exception as e:
            print(f"  ❌ Rule engine error: {e}")
            rule_results = []
        
        # Try neural approach
        print("  → Running neural engine...")
        try:
            neural_results = self.neural_engine.process(query, processed_data=processed_data)
            print(f"  ✅ Neural engine found {len(neural_results)} results")
            if neural_results:
                print(f"     Best neural match: {neural_results[0]['fault']} (confidence: {neural_results[0]['confidence']:.3f})")
        except Exception as e:
            print(f"  ❌ Neural engine error: {e}")
            neural_results = []
        
        # Detect unknown queries
        unknown_detection = self._detect_unknown_query(query, rule_results, neural_results)
        
        if unknown_detection['is_unknown']:
            print(f"  ⚠️ Unknown query detected: {unknown_detection['message']}")
            
            # Apply confidence penalty to all results
            penalty = unknown_detection['confidence_penalty']
            print(f"  📉 Applying {penalty:.0%} confidence penalty for unknown terms")
            
            for result in rule_results:
                result['confidence'] *= penalty
            for result in neural_results:
                result['confidence'] *= penalty
        
        # Combine results
        combined_results = self._combine_results(rule_results, neural_results)
        
        print(f"  🎯 Hybrid result: {len(combined_results)} combined results")
        if combined_results:
            print(f"     Final best match: {combined_results[0]['fault']} (confidence: {combined_results[0]['confidence']:.3f}, source: {combined_results[0]['source']})")
        
        # Return appropriate format based on detection
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
        """
        Detect if the query might be about something not in our knowledge base
        """
        
        # Extract key terms from query
        query_lower = query.lower()
        key_terms = []
        
        # Look for specific equipment/systems that might not be in our database
        specific_equipment = [
            # Water systems
            'seawater', 'sea water', 'raw water', 'ballast', 'bilge', 'freshwater', 'potable water',
            # Propulsion & steering
            'stern tube', 'propeller shaft', 'rudder', 'thruster', 'bow thruster', 'azimuth',
            # Deck equipment
            'winch', 'crane', 'windlass', 'mooring', 'anchor', 'davit', 'hatch', 'ramp',
            # Navigation & electronics  
            'radar', 'sonar', 'gps', 'compass', 'autopilot', 'gyro', 'ecdis', 'vhf', 'radio',
            # HVAC & accommodation
            'ventilation', 'hvac', 'air conditioning', 'galley', 'accommodation', 'cabin',
            # Waste & sanitation
            'sewage', 'waste', 'incinerator', 'garbage', 'sanitary', 'black water', 'grey water',
            # Spaces & structure
            'deck', 'hull', 'superstructure', 'mast', 'bridge', 'engine room', 'workshop',
            'cargo hold', 'tank', 'void space', 'cofferdams',
            # Specific systems
            'hydraulic', 'pneumatic', 'oily water separator', 'ows', 'sewage treatment',
            'reverse osmosis', 'ro plant', 'fresh water generator', 'fwg',
            # Safety systems
            'fire', 'sprinkler', 'foam', 'co2', 'lifeboat', 'life raft', 'emergency',
            'alarm system', 'public address', 'pa system',
            # Cargo systems
            'loading', 'unloading', 'cargo pump', 'manifold', 'pipeline'
        ]
        
        # Check for specific system terms
        for term in specific_equipment:
            if term in query_lower:
                key_terms.append(term)
        
        # Also check for general indicators that suggest non-engine issues
        non_engine_indicators = [
            'room', 'space', 'area', 'compartment', 'leak', 'leakage', 'flooding',
            'fire', 'smoke detector', 'alarm', 'safety', 'emergency', 'spill'
        ]
        
        general_indicators = []
        for indicator in non_engine_indicators:
            if indicator in query_lower and indicator not in ['alarm']:  # 'alarm' can be engine-related
                general_indicators.append(indicator)
        
        print(f"    🔍 Detected specific terms: {key_terms}")
        print(f"    🔍 Non-engine indicators: {general_indicators}")
        
        # If we found specific terms or indicators, check how relevant the results are
        if key_terms or general_indicators:
            all_special_terms = key_terms + general_indicators
            
            # Check if we have any results at all
            total_checked = min(10, len(rule_results) + len(neural_results))
            
            if total_checked == 0:
                # No results at all
                return {
                    'is_unknown': True,
                    'missing_terms': all_special_terms,
                    'confidence_penalty': 0.0,  # No results to penalize
                    'message': f"No faults found related to '{', '.join(all_special_terms)}'. This equipment/system may not be covered in the engine fault database."
                }
            
            # Check relevance of existing results
            relevant_results = 0
            for result in (rule_results + neural_results)[:total_checked]:
                fault_name = result['fault'].lower()
                fault_causes = []
                fault_symptoms = []
                
                # Get causes and symptoms if available
                if 'causes' in result:
                    fault_causes = [str(cause).lower() for cause in result['causes']]
                if 'symptoms' in result:
                    fault_symptoms = [str(symptom).lower() for symptom in result['symptoms']]
                
                # Check if any special terms appear in fault name, causes, or symptoms
                all_fault_text = fault_name + ' ' + ' '.join(fault_causes) + ' ' + ' '.join(fault_symptoms)
                
                # Be stricter about relevance - require exact term matches
                if any(term in all_fault_text for term in all_special_terms):
                    relevant_results += 1
                    print(f"      ✅ Relevant: {fault_name[:50]}...")
                else:
                    print(f"      ❌ Not relevant: {fault_name[:50]}...")
            
            relevance_ratio = relevant_results / total_checked if total_checked > 0 else 0
            
            print(f"    📊 Relevance ratio: {relevance_ratio:.2f} ({relevant_results}/{total_checked})")
            
            # Be more aggressive about detecting unknown queries
            if relevance_ratio == 0.0:
                # No relevant results at all
                return {
                    'is_unknown': True,
                    'missing_terms': all_special_terms,
                    'confidence_penalty': 0.1,  # Reduce to 10% of original confidence
                    'message': f"No engine faults found related to '{', '.join(all_special_terms)}'. The returned results are general engine issues that may not be relevant to your specific query."
                }
            elif relevance_ratio < 0.2:
                # Very few relevant results
                return {
                    'is_unknown': True,
                    'missing_terms': all_special_terms,
                    'confidence_penalty': 0.3,  # Reduce to 30% of original confidence
                    'message': f"Limited engine fault information available for '{', '.join(all_special_terms)}'. Showing general engine faults that may be indirectly related."
                }
            elif relevance_ratio < 0.5:
                # Some relevant results but not many
                return {
                    'is_unknown': True,
                    'missing_terms': all_special_terms,
                    'confidence_penalty': 0.6,  # Reduce to 60% of original confidence
                    'message': f"Some engine faults found related to '{', '.join(all_special_terms)}', but coverage may be limited."
                }
        
        # Check for very low confidence across all results (another indicator)
        all_results = rule_results + neural_results
        if all_results:
            # Normalize rule confidences for comparison
            normalized_confidences = []
            for result in all_results:
                if result.get('source') == 'rule_engine' or 'rule' in result.get('source', ''):
                    # Normalize rule engine confidence (0-20 scale to 0-1)
                    normalized_conf = min(1.0, result['confidence'] / 20.0)
                else:
                    # Neural confidence already 0-1
                    normalized_conf = result['confidence']
                normalized_confidences.append(normalized_conf)
            
            avg_confidence = sum(normalized_confidences) / len(normalized_confidences)
            max_confidence = max(normalized_confidences)
            
            print(f"    📊 Confidence analysis: avg={avg_confidence:.3f}, max={max_confidence:.3f}")
            
            # If average confidence is very low and max confidence is also low
            if avg_confidence < 0.25 and max_confidence < 0.4:
                return {
                    'is_unknown': True,
                    'missing_terms': [],
                    'confidence_penalty': 1.0,  # Don't further reduce already low confidences
                    'message': "Low confidence in all matches. Your query might be about equipment or issues not well covered in the engine fault database."
                }
        
        return {'is_unknown': False}
    
    def _combine_results(self, rule_results, neural_results):
        """
        Intelligently combine results from both engines
        
        Strategy:
        1. Normalize confidence scores to same scale
        2. Compare actual result quality, not just confidence numbers
        3. Prefer results that both engines agree on
        4. Use semantic similarity for final ranking
        """
        
        print(f"    🔄 Combining results:")
        print(f"      Rule results: {len(rule_results)}")
        print(f"      Neural results: {len(neural_results)}")
        
        # Normalize rule engine confidence scores (they're on ~0-20 scale, normalize to 0-1)
        normalized_rule_results = []
        for i, result in enumerate(rule_results):
            normalized_result = result.copy()
            # Rule engine scores typically range 0-20, normalize to 0-1
            original_confidence = result['confidence']
            normalized_confidence = min(1.0, result['confidence'] / 20.0)
            normalized_result['confidence'] = normalized_confidence
            normalized_result['source'] = 'rule_engine_hybrid'
            normalized_rule_results.append(normalized_result)
            
            if i < 3:  # Show first 3
                print(f"        Rule {i+1}: {result['fault'][:40]}... {original_confidence} → {normalized_confidence:.3f}")
        
        # Neural results are already 0-1, just mark them
        normalized_neural_results = []
        for i, result in enumerate(neural_results):
            normalized_result = result.copy()
            normalized_result['source'] = 'neural_engine_hybrid'
            normalized_neural_results.append(normalized_result)
            
            if i < 3:  # Show first 3
                print(f"        Neural {i+1}: {result['fault'][:40]}... {result['confidence']:.3f}")
        
        # Combine all results and handle duplicates
        combined_dict = {}
        
        # First pass: Add all rule results
        for result in normalized_rule_results:
            fault_name = result['fault']
            combined_dict[fault_name] = result
            
        # Second pass: Add neural results and handle duplicates
        for result in normalized_neural_results:
            fault_name = result['fault']
            
            if fault_name not in combined_dict:
                # New fault from neural only, add it
                combined_dict[fault_name] = result
            else:
                # Duplicate found - both engines agree!
                existing = combined_dict[fault_name]
                
                print(f"        🎯 AGREEMENT: {fault_name[:40]}...")
                print(f"          Rule confidence: {existing['confidence']:.3f}")
                print(f"          Neural confidence: {result['confidence']:.3f}")
                
                # Apply boost to the BETTER result
                if result['confidence'] > existing['confidence']:
                    # Neural is better, boost neural result
                    boosted_confidence = min(1.0, result['confidence'] * 1.2)
                    result['confidence'] = boosted_confidence
                    result['source'] = 'both_engines'
                    combined_dict[fault_name] = result
                    print(f"          → Boosted neural: {result['confidence']:.3f}")
                else:
                    # Rule is better, boost rule result
                    boosted_confidence = min(1.0, existing['confidence'] * 1.2)
                    existing['confidence'] = boosted_confidence
                    existing['source'] = 'both_engines'
                    print(f"          → Boosted rule: {existing['confidence']:.3f}")
        
        # Convert back to list and sort by confidence
        combined_list = list(combined_dict.values())
        combined_list.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"    📊 Final ranking:")
        for i, result in enumerate(combined_list[:5]):
            print(f"      {i+1}. {result['fault'][:40]}... {result['confidence']:.3f} ({result['source']})")
        
        # Limit to top 5 results
        return combined_list[:5]
    
    def get_strategy_info(self):
        """Return information about the hybrid strategy"""
        return {
            "strategy": "intelligent_combination_with_unknown_detection",
            "features": [
                "Confidence normalization (rule 0-20 → 0-1)",
                "Agreement detection and boosting",
                "Unknown query detection",
                "Context-specific confidence penalties",
                "Relevance checking for specific equipment terms"
            ],
            "unknown_detection_terms": [
                "seawater", "ballast", "rudder", "thruster", "winch", 
                "crane", "radar", "hvac", "deck", "hull", "etc."
            ],
            "max_results": 5,
            "description": "Combines rule and neural engines intelligently. Detects queries about equipment not in the knowledge base and provides appropriate warnings with confidence adjustments."
        }