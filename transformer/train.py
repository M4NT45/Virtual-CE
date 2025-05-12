from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader
import json
import os

def load_training_data(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def create_training_examples(data):
    examples = []
    
    for item in data:
        query = item['query']
        similar_queries = item['similar_queries']
        
        for similar in similar_queries:
            examples.append(InputExample(texts=[query, similar], label=1.0))
    
    return examples

def train_model():
    # Load base model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Load and prepare training data
    data = load_training_data('data/train_data.json')
    train_examples = create_training_examples(data)
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
    
    # Define training loss
    train_loss = losses.CosineSimilarityLoss(model)
    
    # Train the model
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=3,  # Start with fewer epochs for testing
        warmup_steps=100,
        show_progress_bar=True
    )
    
    # Create directory if it doesn't exist
    os.makedirs('transformer/marine_miniLM', exist_ok=True)
    
    # Save the fine-tuned model
    model.save('transformer/marine_miniLM')
    
if __name__ == "__main__":
    train_model()