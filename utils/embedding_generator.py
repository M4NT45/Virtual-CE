import sys
import os
import pickle

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentence_transformers import SentenceTransformer
from utils.yaml_parser import YamlReader
from models.DB_class import session_maker
from services.input_preprocessing import preprocess_user_query


def generate_embeddings():
    model = SentenceTransformer('transformer/marine_miniLM')
    
    with session_maker() as session:
        yaml_reader = YamlReader(session)
        all_faults = yaml_reader.get_all_faults()
    
    fault_embeddings = {}
    
    for fault in all_faults:
        if 'fault' not in fault:
            continue
            
        name = fault['fault']['name']
        subsystem = fault['fault'].get('subsystem', '')
        
        text_parts = [name]
        symptoms = fault['fault'].get('symptoms', [])
        text_parts.extend(symptoms)
        text = " ".join(text_parts)
        
        processed_text, _ = preprocess_user_query(text)
        embedding = model.encode(processed_text, convert_to_tensor=True)
        
        fault_embeddings[name] = {
            'embedding': embedding,
            'fault': fault,
            'subsystem': subsystem
        }
    
    with open('data/embeddings/fault_embeddings.pkl', 'wb') as f:
        pickle.dump(fault_embeddings, f)


if __name__ == "__main__":
    generate_embeddings()