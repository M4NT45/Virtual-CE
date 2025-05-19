import pickle
from sentence_transformers import SentenceTransformer, util
from services.input_preprocessing import preprocess_user_query

class NeuralEngine:
    def __init__(self):
        print("=== NEURAL ENGINE INITIALIZING WITH SUBSYSTEM FILTERING ===")
        # Load model for query encoding
        self.model = SentenceTransformer('transformer/marine_miniLM')
        
        # Load pre-generated embeddings
        print("Loading pre-generated embeddings...")
        try:
            with open('data/embeddings/fault_embeddings.pkl', 'rb') as f:
                self.fault_embeddings = pickle.load(f)
            print(f"✅ Loaded {len(self.fault_embeddings)} fault embeddings")
        except FileNotFoundError:
            print("❌ Error: fault_embeddings.pkl not found!")
            print("Please run: python embedding_generator.py")
            raise
    
    def process(self, query, processed_data=None):
        # Use preprocessed query if available
        if processed_data and processed_data.get('enhanced_query'):
            processed_query = processed_data['enhanced_query']
        else:
            processed_query, _ = preprocess_user_query(query)
        
        print(f"🔍 Neural Engine Debug:")
        print(f"  Original query: {query}")
        print(f"  Processed query: {processed_query}")
        print(f"  Available faults: {len(self.fault_embeddings)}")
        
        # Determine target subsystem from query
        target_subsystem = None
        query_lower = processed_query.lower()
        
        print(f"  Checking for subsystem in: '{query_lower}'")
        
        if 'main engine' in query_lower or 'main' in query_lower:
            target_subsystem = 'main_engine'
            print(f"  Detected: main_engine")
        elif any(term in query_lower for term in ['auxiliary engine', 'aux engine', 'auxiliary', 'aux']):
            target_subsystem = 'auxiliary_engine'
            print(f"  Detected: auxiliary_engine")
        elif any(term in query_lower for term in ['generator', 'gen', 'genset']):
            target_subsystem = 'generator'
            print(f"  Detected: generator")
            
        print(f"  Target subsystem: {target_subsystem}")
        
        # Debug: Check what subsystems are actually in the data
        available_subsystems = set()
        for name, data in self.fault_embeddings.items():
            sub = data.get('subsystem', '')
            if sub:
                available_subsystems.add(sub)
        print(f"  Available subsystems in data: {sorted(available_subsystems)}")
        
        # Encode query
        query_embedding = self.model.encode(processed_query, convert_to_tensor=True)
        print(f"  Query embedding shape: {query_embedding.shape}")
        
        # Calculate similarities with subsystem filtering
        results = []
        similarities_debug = []
        filtered_count = 0
        
        for name, data in self.fault_embeddings.items():
            # Get subsystem from stored data
            fault_subsystem = data.get('subsystem', '')
            
            # If we have a target subsystem, filter by it
            if target_subsystem and fault_subsystem:
                if target_subsystem != fault_subsystem:
                    filtered_count += 1
                    continue  # Skip faults from different subsystems
            
            # Make sure both embeddings are tensors
            fault_embedding = data['embedding']
            if not hasattr(fault_embedding, 'shape'):
                # Convert to tensor if it's not already
                import torch
                fault_embedding = torch.tensor(fault_embedding)
            
            # Calculate similarity
            similarity = util.pytorch_cos_sim(query_embedding, fault_embedding).item()
            similarities_debug.append((name, similarity, fault_subsystem))
            
            if similarity > 0.3:  # Threshold for relevance
                results.append({
                    'fault': name,
                    'confidence': float(similarity),
                    'causes': data['fault']['fault'].get('causes', []),
                    'actions': data['fault']['fault'].get('actions', []),
                    'symptoms': data['fault']['fault'].get('symptoms', []),
                    'source': 'neural_engine',
                    'source_file': data['fault'].get('_source_file', 'unknown'),
                    'fault_number': data['fault'].get('_fault_number', 0),
                    'subsystem': fault_subsystem
                })
        
        print(f"  Filtered out {filtered_count} faults due to subsystem mismatch")
        
        # Debug: Show similarity distribution
        similarities_debug.sort(key=lambda x: x[1], reverse=True)
        print(f"  Top 5 similarities (after filtering):")
        for name, sim, subsys in similarities_debug[:5]:
            print(f"    {name} ({subsys}): {sim:.3f}")
        
        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"  Results above threshold (0.3): {len(results)}")
        
        # Debug: Show what we're returning
        if results:
            print(f"  Returning {len(results)} results:")
            for i, result in enumerate(results):
                print(f"    {i+1}. {result['fault']} (confidence: {result['confidence']:.3f}) - {result.get('subsystem', 'unknown')}")
                print(f"       Causes: {len(result.get('causes', []))}")
                print(f"       Actions: {len(result.get('actions', []))}")
        else:
            print("  No results above threshold!")
        
        # Return same format as rule engine - just the list of faults
        return results