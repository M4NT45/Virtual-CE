import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pickle
from sentence_transformers import SentenceTransformer
from utils.yaml_parser import YamlReader
from models.DB_class import session_maker
from services.input_preprocessing import preprocess_user_query

def generate_embeddings():
    """Generate and save embeddings for all fault cases - SIMPLE VERSION"""
    
    # Load model
    print("Loading model...")
    model = SentenceTransformer('transformer/marine_miniLM')
    
    # Get fault data
    print("Loading fault data...")
    with session_maker() as session:
        yaml_reader = YamlReader(session)
        all_faults = yaml_reader.get_all_faults()
    
    # Generate embeddings
    print(f"Generating embeddings for {len(all_faults)} faults...")
    fault_embeddings = {}
    
    for i, fault in enumerate(all_faults):
        if 'fault' not in fault:
            continue
            
        name = fault['fault']['name']
        subsystem = fault['fault'].get('subsystem', '')
        
        # Simple approach - just name + symptoms
        text_parts = [name]
        symptoms = fault['fault'].get('symptoms', [])
        text_parts.extend(symptoms)
        text = " ".join(text_parts)
        
        print(f"Processing ({i+1}/{len(all_faults)}): {name}")
        print(f"  Subsystem: {subsystem}")
        print(f"  Text: {text[:100]}...")
        
        # Preprocess and encode
        processed_text, _ = preprocess_user_query(text)
        embedding = model.encode(processed_text, convert_to_tensor=True)
        
        # Store with subsystem for filtering
        fault_embeddings[name] = {
            'embedding': embedding,
            'fault': fault,
            'subsystem': subsystem
        }
    
    # Save
    with open('data/embeddings/fault_embeddings.pkl', 'wb') as f:
        pickle.dump(fault_embeddings, f)
    
    print(f"Done! Saved {len(fault_embeddings)} embeddings")

if __name__ == "__main__":
    generate_embeddings()