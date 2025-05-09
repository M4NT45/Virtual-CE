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