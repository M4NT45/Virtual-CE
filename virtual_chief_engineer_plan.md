# Virtual Chief Engineer Implementation Plan

## Project Overview

The Virtual Chief Engineer is a web-based intelligent assistant that helps marine engineers diagnose and troubleshoot machinery faults. It combines rule-based expert logic with a lightweight neural model to deliver reliable and flexible responses to technical issues in natural language.

## Complete File Structure

```
virtual_chief_engineer/
├── .gitignore
├── README.md
├── requirements.txt
├── app.py                  # Main Flask application
├── config.py               # Configuration settings
├── static/                 # Static files (CSS, JS)
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
├── templates/              # HTML templates
│   ├── index.html
│   ├── results.html
│   └── base.html
├── models/                 # Database models
│   ├── __init__.py
│   └── schema.py
├── knowledge_base/         # YAML fault trees
│   ├── main_engine/
│   │   ├── high_temperature.yaml
│   │   ├── low_pressure.yaml
│   │   └── excessive_vibration.yaml
│   ├── purifier/
│   │   ├── vibration.yaml
│   │   └── overflow.yaml
│   ├── fuel_system/
│   │   ├── contamination.yaml
│   │   └── pressure_drop.yaml
│   ├── air_compressors/
│   │   ├── overheating.yaml
│   │   └── high_moisture.yaml
│   └── pumps_coolers/
│       ├── cavitation.yaml
│       └── leakage.yaml
├── services/               # Business logic
│   ├── __init__.py
│   ├── rule_engine.py
│   ├── neural_engine.py
│   └── hybrid_engine.py
├── utils/                  # Helper functions
│   ├── __init__.py
│   ├── yaml_parser.py
│   ├── db_init.py
│   └── response_formatter.py
├── transformer/            # Transformer model code
│   ├── __init__.py
│   ├── model.py
│   ├── train.py
│   ├── inference.py
│   └── model/              # Directory for saved models
│       └── marine_miniLM/
├── data/                   # Training and test data
│   ├── train_data.json
│   ├── test_data.json
│   └── embeddings/
└── tests/                  # Unit and integration tests
    ├── __init__.py
    ├── test_rule_engine.py
    ├── test_neural_engine.py
    └── test_api.py
```

## Implementation Plan

### Phase 1: Core Setup (Week 1)

#### Day 1-2: Project Initialization

1. **Set up project structure**
   - Create all the directories as outlined in the project structure
   - Set up virtual environment: `python -m venv venv`
   - Activate environment and install basic dependencies:
     ```
     pip install flask flask-sqlalchemy pyyaml sentence-transformers
     pip freeze > requirements.txt
     ```
   - Initialize Git repository (if not already done)

2. **Create minimal Flask application**
   ```python
   # app.py
   from flask import Flask, render_template, jsonify
   
   app = Flask(__name__)
   
   @app.route('/')
   def index():
       return render_template('index.html')
   
   @app.route('/api/health')
   def health_check():
       return jsonify({"status": "healthy"})
   
   if __name__ == '__main__':
       app.run(debug=True)
   ```

3. **Create basic HTML template**
   ```html
   <!-- templates/index.html -->
   <!DOCTYPE html>
   <html>
   <head>
       <title>Virtual Chief Engineer</title>
   </head>
   <body>
       <h1>Virtual Chief Engineer</h1>
       <form id="query-form">
           <textarea id="query" placeholder="Describe the machinery issue..."></textarea>
           <button type="submit">Diagnose</button>
       </form>
       <div id="results"></div>
       
       <script src="{{ url_for('static', filename='js/main.js') }}"></script>
   </body>
   </html>
   ```

4. **Create basic JavaScript file**
   ```javascript
   // static/js/main.js
   document.addEventListener('DOMContentLoaded', function() {
       const form = document.getElementById('query-form');
       const resultsDiv = document.getElementById('results');
       
       form.addEventListener('submit', function(e) {
           e.preventDefault();
           
           const query = document.getElementById('query').value;
           
           fetch('/api/diagnose', {
               method: 'POST',
               headers: {
                   'Content-Type': 'application/json',
               },
               body: JSON.stringify({query: query}),
           })
           .then(response => response.json())
           .then(data => {
               resultsDiv.innerHTML = '<h2>Diagnosis Results</h2>';
               
               if (data.length === 0) {
                   resultsDiv.innerHTML += '<p>No matching faults found. Please provide more details.</p>';
               } else {
                   data.forEach(result => {
                       resultsDiv.innerHTML += `
                           <div class="result">
                               <h3>${result.fault}</h3>
                               <p>Confidence: ${(result.confidence * 100).toFixed(2)}%</p>
                               <h4>Possible Causes:</h4>
                               <ul>
                                   ${result.causes.map(cause => `
                                       <li>
                                           <strong>${cause.name}</strong>
                                           <h5>Checks:</h5>
                                           <ul>
                                               ${cause.checks.map(check => `<li>${check}</li>`).join('')}
                                           </ul>
                                           <h5>Actions:</h5>
                                           <ul>
                                               ${cause.actions.map(action => `<li>${action}</li>`).join('')}
                                           </ul>
                                       </li>
                                   `).join('')}
                               </ul>
                           </div>
                       `;
                   });
               }
           })
           .catch(error => {
               resultsDiv.innerHTML = `<p>Error: ${error.message}</p>`;
           });
       });
   });
   ```

#### Day 3-4: Database Setup

1. **Create SQLite database configuration**
   ```python
   # config.py
   import os
   
   class Config:
       SQLALCHEMY_DATABASE_URI = 'sqlite:///virtual_chief.db'
       SQLALCHEMY_TRACK_MODIFICATIONS = False
       SECRET_KEY = 'your-secret-key'
   ```

2. **Implement database models**
   ```python
   # models/schema.py
   from flask_sqlalchemy import SQLAlchemy
   from datetime import datetime
   
   db = SQLAlchemy()
   
   class YamlPath(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       subsystem = db.Column(db.String(100), nullable=False)
       path = db.Column(db.String(255), nullable=False)
       description = db.Column(db.Text)
       created_at = db.Column(db.DateTime, default=datetime.utcnow)
   
   class Query(db.Model):
       id = db.Column(db.Integer, primary_key=True)
       text = db.Column(db.Text, nullable=False)
       timestamp = db.Column(db.DateTime, default=datetime.utcnow)
   ```

3. **Update Flask app with database integration**
   ```python
   # app.py (updated)
   from flask import Flask, render_template, jsonify, request
   from models.schema import db, YamlPath, Query
   
   app = Flask(__name__)
   app.config.from_object('config.Config')
   
   db.init_app(app)
   
   # ... routes ...
   
   if __name__ == '__main__':
       with app.app_context():
           db.create_all()
       app.run(debug=True)
   ```

4. **Create a script to populate YAML paths**
   ```python
   # utils/db_init.py
   import os
   from flask import Flask
   from models.schema import db, YamlPath
   
   def init_db():
       app = Flask(__name__)
       app.config.from_object('config.Config')
       db.init_app(app)
       
       with app.app_context():
           db.create_all()
           
           # Add sample paths
           subsystems = ['main_engine', 'purifier', 'fuel_system', 'air_compressors', 'pumps_coolers']
           for subsystem in subsystems:
               path = f'knowledge_base/{subsystem}'
               yaml_path = YamlPath(subsystem=subsystem, path=path)
               db.session.add(yaml_path)
           
           db.session.commit()
   
   if __name__ == '__main__':
       init_db()
   ```

### Phase 2: Knowledge Base Foundation (Week 1-2)

#### Day 5-7: Create YAML Structure and Sample Data

1. **Define YAML structure for fault trees**
   ```yaml
   # knowledge_base/main_engine/high_temperature.yaml
   fault:
     name: "Main Engine High Temperature"
     symptoms:
       - "High jacket water temperature"
       - "High exhaust gas temperature"
       - "High lubricating oil temperature"
     
     causes:
       - name: "Cooling system malfunction"
         probability: 0.8
         checks:
           - "Check coolant level"
           - "Inspect cooling pump operation"
           - "Check heat exchanger for fouling"
         actions:
           - "Refill coolant if low"
           - "Clean heat exchanger"
           - "Replace cooling pump if faulty"
       
       - name: "Excessive load"
         probability: 0.6
         checks:
           - "Check engine load indicator"
           - "Review recent operating conditions"
         actions:
           - "Reduce load if possible"
           - "Check for propeller fouling"
   ```

2. **Create multiple sample fault trees**
   - Create at least 5-10 sample YAML files across different subsystems
   - Focus on common marine machinery issues

3. **Implement YAML parser utility**
   ```python
   # utils/yaml_parser.py
   import os
   import yaml
   from models.schema import YamlPath, db
   
   class YamlReader:
       def __init__(self):
           self.yaml_paths = {}
           self._load_paths_from_db()
       
       def _load_paths_from_db(self):
           paths = YamlPath.query.all()
           for path in paths:
               self.yaml_paths[path.subsystem] = path.path
       
       def get_fault_tree(self, subsystem, fault_name):
           base_path = self.yaml_paths.get(subsystem)
           if not base_path:
               return None
           
           file_path = os.path.join(base_path, f"{fault_name}.yaml")
           if not os.path.exists(file_path):
               return None
           
           with open(file_path, 'r') as file:
               return yaml.safe_load(file)
       
       def get_all_faults(self, subsystem=None):
           results = []
           
           if subsystem:
               subsystems = [subsystem]
           else:
               subsystems = self.yaml_paths.keys()
           
           for sys in subsystems:
               base_path = self.yaml_paths.get(sys)
               if not base_path or not os.path.exists(base_path):
                   continue
               
               for filename in os.listdir(base_path):
                   if filename.endswith('.yaml'):
                       with open(os.path.join(base_path, filename), 'r') as file:
                           fault_data = yaml.safe_load(file)
                           results.append(fault_data)
           
           return results
   ```

### Phase 3: Rule-Based Engine (Week 2)

#### Day 8-10: Implement Rule Engine

1. **Create rule engine service**
   ```python
   # services/rule_engine.py
   from utils.yaml_parser import YamlReader
   
   class RuleEngine:
       def __init__(self):
           self.yaml_reader = YamlReader()
       
       def process(self, query):
           # For MVP: simple keyword matching
           query_words = set(query.lower().split())
           all_faults = self.yaml_reader.get_all_faults()
           
           results = []
           for fault in all_faults:
               score = self._calculate_match_score(query_words, fault)
               if score > 0:
                   results.append({
                       'fault': fault['fault']['name'],
                       'confidence': score,
                       'causes': fault['fault']['causes'],
                       'source': 'rule_engine'
                   })
           
           # Sort by confidence score
           results.sort(key=lambda x: x['confidence'], reverse=True)
           return results
       
       def _calculate_match_score(self, query_words, fault):
           # Extract all symptoms
           symptoms = fault['fault']['symptoms']
           symptom_words = set()
           for symptom in symptoms:
               symptom_words.update(symptom.lower().split())
           
           # Count matching words
           matches = query_words.intersection(symptom_words)
           
           # Simple score: proportion of matching words
           if len(symptom_words) > 0:
               return len(matches) / len(symptom_words)
           return 0
   ```

2. **Update Flask app to use rule engine**
   ```python
   # Add to app.py
   from services.rule_engine import RuleEngine
   
   rule_engine = RuleEngine()
   
   @app.route('/api/diagnose', methods=['POST'])
   def diagnose():
       user_query = request.json.get('query', '')
       
       # Log the query to database
       query_record = Query(text=user_query)
       db.session.add(query_record)
       db.session.commit()
       
       # Process with rule engine
       results = rule_engine.process(user_query)
       
       return jsonify(results)
   ```

### Phase 4: Transformer Model Foundation (Week 3)

#### Day 11-14: Prepare for Transformer Fine-tuning

1. **Create dataset structure**
   ```json
   // data/train_data.json
   [
     {
       "query": "Main engine temperature is higher than normal",
       "similar_queries": [
         "Engine is running hot",
         "High temperature alarm on main engine",
         "ME temp gauge showing above normal range",
         "Main engine overheating"
       ],
       "fault": "main_engine/high_temperature"
     },
     {
       "query": "Fuel oil purifier vibrating excessively",
       "similar_queries": [
         "Purifier has strong vibration",
         "FO purifier shaking during operation",
         "Abnormal vibration from fuel purifier",
         "Purifier making unusual vibration"
       ],
       "fault": "purifier/excessive_vibration"
     }
     // Add at least 10-15 examples to start
   ]
   ```

2. **Implement basic model training script**
   ```python
   # transformer/train.py
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
       os.makedirs('transformer/model', exist_ok=True)
       
       # Save the fine-tuned model
       model.save('transformer/model/marine_miniLM')
       
   if __name__ == "__main__":
       train_model()
   ```

### Phase 5: Neural Engine Implementation (Week 4)

1. **Implement neural engine service**
   ```python
   # services/neural_engine.py
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
   ```

2. **Implement model inference utility**
   ```python
   # transformer/inference.py
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
   ```

### Phase 6: Hybrid Engine Integration (Week 5)

1. **Implement hybrid engine service**
   ```python
   # services/hybrid_engine.py
   from services.rule_engine import RuleEngine
   from services.neural_engine import NeuralEngine
   
   class HybridEngine:
       def __init__(self):
           self.rule_engine = RuleEngine()
           self.neural_engine = NeuralEngine()
       
       def process(self, query):
           # First try rule-based approach
           rule_results = self.rule_engine.process(query)
           
           # If confident results found, return them
           if rule_results and rule_results[0]['confidence'] > 0.7:
               return rule_results
           
           # Otherwise, fall back to neural approach
           neural_results = self.neural_engine.process(query)
           
           # Combine and rank results
           combined_results = self._combine_results(rule_results, neural_results)
           
           return combined_results
       
       def _combine_results(self, rule_results, neural_results):
           # Start with a dictionary to track unique faults
           combined_dict = {}
           
           # Add rule results first
           for result in rule_results:
               fault_name = result['fault']
               if fault_name not in combined_dict:
                   combined_dict[fault_name] = result
               else:
                   # Keep highest confidence
                   if result['confidence'] > combined_dict[fault_name]['confidence']:
                       combined_dict[fault_name] = result
           
           # Then neural results (will override rule results if higher confidence)
           for result in neural_results:
               fault_name = result['fault']
               if fault_name not in combined_dict:
                   combined_dict[fault_name] = result
               else:
                   # Apply a slight bias towards rule engine (more reliable)
                   neural_confidence = result['confidence']
                   rule_confidence = combined_dict[fault_name].get('confidence', 0)
                   
                   if neural_confidence > rule_confidence * 1.1:  # 10% threshold to override
                       combined_dict[fault_name] = result
           
           # Convert back to list and sort
           combined_list = list(combined_dict.values())
           combined_list.sort(key=lambda x: x['confidence'], reverse=True)
           
           return combined_list
   ```

2. **Update Flask app to use hybrid engine**
   ```python
   # app.py (updated)
   from services.hybrid_engine import HybridEngine
   
   hybrid_engine = HybridEngine()
   
   @app.route('/api/diagnose', methods=['POST'])
   def diagnose():
       user_query = request.json.get('query', '')
       
       # Log the query to database
       query_record = Query(text=user_query)
       db.session.add(query_record)
       db.session.commit()
       
       # Process with hybrid engine
       results = hybrid_engine.process(user_query)
       
       return jsonify(results)
   ```

### Phase 7: Frontend Enhancement (Week 6)

1. **Improve HTML/CSS**
   - Create a responsive layout
   - Add styling for diagnosis results
   - Implement loading indicators

2. **Enhance JavaScript functionality**
   - Add input validation
   - Implement dynamic result rendering
   - Add history of previous queries

### Phase 8: Testing and Refinement (Week 7-8)

1. **Create test cases**
   - Write unit tests for each component
   - Implement integration tests
   - Create test dataset for system evaluation

2. **Performance optimization**
   - Optimize database queries
   - Implement caching for frequent queries
   - Enhance transformer model performance

3. **Expand knowledge base**
   - Add more fault trees
   - Refine existing fault descriptions
   - Improve symptom-cause mappings

### Phase 9: Documentation and Deployment (Week 9-10)

1. **Create comprehensive documentation**
   - User guide
   - API documentation
   - System architecture document

2. **Prepare deployment**
   - Configure production environment
   - Set up error logging
   - Implement security measures

3. **Create presentation**
   - Prepare slides
   - Create demonstration scenarios
   - Compile project metrics and results

## Starting Point: Initial Tasks

To get started immediately:

1. **Set up your development environment**
   - Create virtual environment
   - Install basic dependencies
   - Create the basic directory structure

2. **Create minimal Flask app**
   - Implement the simple app.py described above
   - Add basic HTML template
   - Test that your app runs properly

3. **Set up database**
   - Implement SQLite configuration
   - Create database models
   - Initialize the database
