from sentence_transformers import SentenceTransformer, util
from utils.yaml_parser import YamlReader
from models.DB_class import session_maker

class NeuralEngine:
    def __init__(self):
        self.model = SentenceTransformer('transformer/model/marine_miniLM')
        self.session_maker = session_maker
        self.fault_embeddings = {}
        self._precompute_embeddings()
        
    def _precompute_embeddings(self):
        # Precompute embeddings for all faults
        with self.session_maker() as session:
            yaml_reader = YamlReader(session)
            all_faults = yaml_reader.get_all_faults()
            
            for fault in all_faults:
                if 'fault' not in fault:
                    continue
                    
                name = fault['fault']['name']
                
                # Create text representation for embedding
                text = name + " "
                
                # Add symptoms to text
                symptoms = fault['fault'].get('symptoms', [])
                for symptom in symptoms:
                    text += symptom + " "
                
                # Generate embedding
                embedding = self.model.encode(text, convert_to_tensor=True)
                
                self.fault_embeddings[name] = {
                    'embedding': embedding,
                    'fault': fault
                }
    
    def process(self, query):
        # Encode query
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        
        # Calculate similarities
        results = []
        for name, data in self.fault_embeddings.items():
            similarity = util.pytorch_cos_sim(query_embedding, data['embedding']).item()
            
            if similarity > 0.3:  # Threshold for relevance
                results.append({
                    'fault': name,
                    'confidence': float(similarity),
                    'causes': data['fault']['fault'].get('causes', []),
                    'source': 'neural_engine',
                    'source_file': data['fault'].get('_source_file', 'unknown'),
                    'fault_number': data['fault'].get('_fault_number', 0)
                })
        
        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results