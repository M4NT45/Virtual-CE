import pickle
from sentence_transformers import SentenceTransformer, util
from services.input_preprocessing import preprocess_user_query

class NeuralEngine:
    def __init__(self):
        self.model = SentenceTransformer('transformer/marine_miniLM')
        
        try:
            with open('data/embeddings/fault_embeddings.pkl', 'rb') as f:
                self.fault_embeddings = pickle.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("Embeddings file not found. Please run: python embedding_generator.py")
    
    def process(self, query, processed_data=None):
        if processed_data and processed_data.get('enhanced_query'):
            processed_query = processed_data['enhanced_query']
        else:
            processed_query, _ = preprocess_user_query(query)
        
        target_subsystem = None
        query_lower = processed_query.lower()
        
        if 'main engine' in query_lower or 'main' in query_lower:
            target_subsystem = 'main_engine'
        elif any(term in query_lower for term in ['auxiliary engine', 'aux engine', 'auxiliary', 'aux', 'generator', 'gen', 'genset']):
            target_subsystem = 'auxiliary_engine'
        
        query_embedding = self.model.encode(processed_query, convert_to_tensor=True)
        
        results = []
        for name, data in self.fault_embeddings.items():
            fault_subsystem = data.get('subsystem', '')
            
            if target_subsystem and fault_subsystem:
                if target_subsystem != fault_subsystem:
                    continue
            
            fault_embedding = data['embedding']
            if not hasattr(fault_embedding, 'shape'):
                import torch
                fault_embedding = torch.tensor(fault_embedding)
            
            similarity = util.pytorch_cos_sim(query_embedding, fault_embedding).item()
            
            if similarity > 0.3:
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
        
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results