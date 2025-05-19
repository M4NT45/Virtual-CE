import pickle
import torch

# Check the embedding format
print("=== Checking Embedding Format ===")

with open('data/embeddings/fault_embeddings.pkl', 'rb') as f:
    fault_embeddings = pickle.load(f)

# Check first embedding
first_fault = list(fault_embeddings.keys())[0]
first_data = fault_embeddings[first_fault]

print(f"First fault: {first_fault}")
print(f"Keys in data: {list(first_data.keys())}")

embedding = first_data['embedding']
print(f"Embedding type: {type(embedding)}")
print(f"Embedding shape: {getattr(embedding, 'shape', 'No shape attribute')}")
print(f"Is tensor? {torch.is_tensor(embedding)}")

if torch.is_tensor(embedding):
    print(f"Tensor device: {embedding.device}")
    print(f"Tensor dtype: {embedding.dtype}")
    print(f"First 5 values: {embedding[:5]}")
else:
    print(f"Embedding is: {type(embedding)}")
    if hasattr(embedding, '__len__'):
        print(f"Length: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")

# Test similarity calculation manually
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('transformer/marine_miniLM')
test_query = "main engine overheating"
query_embedding = model.encode(test_query, convert_to_tensor=True)

print(f"\nQuery embedding shape: {query_embedding.shape}")
print(f"Query embedding type: {type(query_embedding)}")

# Calculate similarity manually
similarity = util.pytorch_cos_sim(query_embedding, embedding).item()
print(f"Manual similarity calculation: {similarity:.6f}")

# Check if all similarities are high
print("\n=== Testing similarity with different embeddings ===")
for i, (name, data) in enumerate(list(fault_embeddings.items())[:5]):
    emb = data['embedding']
    sim = util.pytorch_cos_sim(query_embedding, emb).item()
    print(f"{name}: {sim:.6f}")
    if i >= 4:
        break