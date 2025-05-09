from flask import Flask, render_template, jsonify, request
from models.schema import db, YamlPath, Query

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)