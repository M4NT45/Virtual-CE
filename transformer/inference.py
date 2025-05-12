from sentence_transformers import SentenceTransformer, util
import torch

class MarineTransformer:
    def __init__(self, model_path='transformer/model/marine_miniLM'):
        self.model = SentenceTransformer(model_path)
    
    def encode(self, text):
        return self.model.encode(text, convert_to_tensor=True)
    
    def calculate_similarity(self, text1, text2):
        embedding1 = self.encode(text1)
        embedding2 = self.encode(text2)
        
        return util.pytorch_cos_sim(embedding1, embedding2).item()
    
    def find_most_similar(self, query, candidates):
        query_embedding = self.encode(query)
        
        similarities = []
        for candidate in candidates:
            candidate_embedding = self.encode(candidate)
            similarity = util.pytorch_cos_sim(query_embedding, candidate_embedding).item()
            similarities.append((candidate, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities