# Quick test to check if embeddings have subsystem info
import pickle

print("=== Checking Embeddings Structure ===")

with open('data/embeddings/fault_embeddings.pkl', 'rb') as f:
    fault_embeddings = pickle.load(f)

# Check first few faults
for i, (name, data) in enumerate(list(fault_embeddings.items())[:5]):
    print(f"\n{i+1}. Fault: {name}")
    print(f"   Keys: {list(data.keys())}")
    if 'subsystem' in data:
        print(f"   Subsystem: {data['subsystem']}")
    else:
        print(f"   Subsystem: NOT FOUND!")
    
# Check all available subsystems
subsystems = set()
for name, data in fault_embeddings.items():
    sub = data.get('subsystem', '')
    if sub:
        subsystems.add(sub)

print(f"\n=== All Subsystems in Data ===")
print(sorted(subsystems))

# Test query processing
query = "auxiliary engine engine temperature high"
query_lower = query.lower()

print(f"\n=== Testing Subsystem Detection ===")
print(f"Query: {query}")
print(f"Query lower: {query_lower}")

target_subsystem = None
if 'main engine' in query_lower or 'main' in query_lower:
    target_subsystem = 'main_engine'
    print("Detected: main_engine")
elif any(term in query_lower for term in ['auxiliary engine', 'aux engine', 'auxiliary', 'aux']):
    target_subsystem = 'auxiliary_engine'
    print("Detected: auxiliary_engine")
elif any(term in query_lower for term in ['generator', 'gen', 'genset']):
    target_subsystem = 'generator'
    print("Detected: generator")

print(f"Final target_subsystem: {target_subsystem}")

# Check if there are auxiliary engine faults
aux_faults = [name for name, data in fault_embeddings.items() if data.get('subsystem') == 'auxiliary_engine']
print(f"\nAuxiliary engine faults found: {len(aux_faults)}")
if aux_faults:
    print("Examples:")
    for fault in aux_faults[:3]:
        print(f"  - {fault}")
else:
    print("NO AUXILIARY ENGINE FAULTS FOUND!")
    
    # Check what subsystems we actually have
    main_faults = [name for name, data in fault_embeddings.items() if data.get('subsystem') == 'main_engine']
    print(f"Main engine faults: {len(main_faults)}")
    
    # Maybe the subsystem names are different?
    print("\nAll faults with 'auxiliary' in name:")
    for name, data in fault_embeddings.items():
        if 'auxiliary' in name.lower():
            print(f"  - {name} (subsystem: '{data.get('subsystem', 'NONE')}')")