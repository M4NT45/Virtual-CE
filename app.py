from flask import Flask, render_template, jsonify, request, session
from sqlalchemy import select
from models.DB_class import session_maker
from models.query_class import Query
from services.rule_engine import RuleEngine
from services.neural_engine import NeuralEngine
from services.hybrid_engine import HybridEngine
from services.input_preprocessing import process_query
import uuid
import time

app = Flask(__name__)
app.config.from_object('config.Config')
app.secret_key = 'your_secret_key_here'

rule_engine = RuleEngine()
neural_engine = NeuralEngine()
hybrid_engine = HybridEngine()

@app.route('/')
def index():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['conversation_state'] = {
            "awaiting_clarification": None,
            "original_query": None,
            "clarified_engine": None,
            "timestamp": time.time()
        }
    return render_template('index.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/api/diagnose', methods=['POST'])
def diagnose():
    data = request.json
    user_query = data.get('query', '')
    engine_type = data.get('engine', 'hybrid')
    
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        session['conversation_state'] = {
            "awaiting_clarification": None,
            "original_query": None,
            "clarified_engine": None,
            "timestamp": time.time()
        }
    
    conversation_state = session.get('conversation_state')
        
    query_result = process_query(user_query, conversation_state)
    
    with session_maker() as db_session:
        query_record = Query(
            text=user_query,
            clarification_requested=query_result.get('needs_clarification', False),
            clarification_type=query_result.get('awaiting_clarification'),
            processed_text=query_result.get('processed_query'),
            enhanced_text=query_result.get('enhanced_query'),
            engine_type=engine_type,
            parent_query_id=conversation_state.get('last_query_id')
        )
        db_session.add(query_record)
        db_session.commit()
        last_query_id = query_record.id
    
    session['conversation_state'] = {
        "awaiting_clarification": query_result.get('awaiting_clarification'),
        "original_query": query_result.get('original_query_for_clarification'),
        "clarified_engine": query_result.get('clarified_engine'),
        "timestamp": time.time(),
        "last_query_id": last_query_id
    }
    
    if query_result.get('needs_clarification', False):
        return jsonify({
            "type": "clarification",
            "message": query_result.get('clarification_message'),
            "awaiting": query_result.get('awaiting_clarification')
        })
    
    enhanced_query = query_result.get('enhanced_query')
    
    if engine_type == 'rule':
        diagnostic_results = rule_engine.process(enhanced_query, processed_data=query_result)
    elif engine_type == 'neural':
        diagnostic_results = neural_engine.process(enhanced_query, processed_data=query_result)
    else:
        diagnostic_results = hybrid_engine.process(enhanced_query, processed_data=query_result)
        
    return jsonify(diagnostic_results)

@app.route('/api/reset_conversation', methods=['POST'])
def reset_conversation():
    """Reset the conversation state (for testing or when user wants to start over)"""
    session['conversation_state'] = {
        "awaiting_clarification": None,
        "original_query": None,
        "clarified_engine": None,
        "timestamp": time.time()
    }
    return jsonify({"status": "success", "message": "Conversation reset"})

if __name__ == '__main__':
    app.run(debug=True)