from flask import Flask, render_template, jsonify, request
from models.schema import db, YamlPath, Query
from services.rule_engine import RuleEngine
from services.neural_engine import NeuralEngine
from services.hybrid_engine import HybridEngine

app = Flask(__name__)
# app.config.from_object('config.Config')

# db.init_app(app)

# rule_engine = RuleEngine()
# neural_engine = NeuralEngine()
# hybrid_engine = HybridEngine()

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/api/diagnose', methods=['POST'])
# def diagnose():
#     user_query = request.json.get('query', '')
    
#     # Log the query to database
#     query_record = Query(text=user_query)
#     db.session.add(query_record)
#     db.session.commit()
    
#     # Process with hybrid engine
#     results = hybrid_engine.process(user_query)
    
#     return jsonify(results)

# @app.route('/api/health')
# def health_check():
#     return jsonify({"status": "healthy"})

if __name__ == '__main__':
    # with app.app_context():
    #     db.create_all()
    app.run(debug=True)