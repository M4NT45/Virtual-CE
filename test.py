from services.neural_engine import NeuralEngine

# Test the neural engine directly
print("=== Testing Neural Engine ===")

neural_engine = NeuralEngine()

# Test with simple queries
test_queries = [
    "main engine overheating",
    "high temperature",
    "engine hot",
    "purifier not working",
    "fuel pump",
    "cooling system"
]

for query in test_queries:
    print(f"\n🔍 Testing query: '{query}'")
    results = neural_engine.process(query)
    
    if results['faults']:
        print(f"  ✅ Found {len(results['faults'])} matches")
        for i, fault in enumerate(results['faults'][:3]):  # Show top 3
            print(f"    {i+1}. {fault['fault']} (confidence: {fault['confidence']:.3f})")
    else:
        print(f"  ❌ No matches found above threshold")
        print(f"  Processed query: {results.get('processed_query')}")

print("\n=== Test Complete ===")