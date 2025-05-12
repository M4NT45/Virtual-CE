from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np
from utils.yaml_parser import YamlReader

class NeuralEngine:
    def __init__(self):
        self.model = SentenceTransformer('transformer/model/marine_miniLM')
        self.yaml_reader = YamlReader()
        self.fault_embeddings = {}
        self._precompute_embeddings()
    
    def _precompute_embeddings(self):
        # Precompute embeddings for all faults
        all_faults = self.yaml_reader.get_all_faults()
        for fault in all_faults:
            name = fault['fault']['name']
            
            # Create text representation for embedding
            text = name + " "
            for symptom in fault['fault']['symptoms']:
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
                    'causes': data['fault']['fault']['causes'],
                    'source': 'neural_engine'
                })
        
        # Sort by confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results