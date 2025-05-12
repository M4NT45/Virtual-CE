from flask import Flask, render_template, jsonify, request
from sqlalchemy import select

from models.DB_class import session_maker
from models.yaml_path_class import YamlPath
from models.query_class import Query

from services.rule_engine import RuleEngine
from services.neural_engine import NeuralEngine
from services.hybrid_engine import HybridEngine

app = Flask(__name__)
app.config.from_object('config.Config')

# rule_engine = RuleEngine()
# neural_engine = NeuralEngine()
# hybrid_engine = HybridEngine()

@app.route('/')
def index():
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# @app.route('/api/diagnose', methods=['POST'])
# def diagnose():
#     data = request.json
#     user_query = data.get('query', '')
#     engine_type = data.get('engine', 'hybrid')
    
#     with session_maker() as session:
#         query_record = Query(text=user_query)
#         session.add(query_record)
#         session.commit()
        
#     if engine_type == 'rule':
#         results = rule_engine.process(user_query)
#     elif engine_type == 'neural':
#         results = neural_engine.process(user_query)
#     else:  # hybrid
#         results = hybrid_engine.process(user_query)

if __name__ == '__main__':
    app.run(debug=True)