import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from models.DB_class import session_maker
from models.yaml_path_class import YamlPath

def seed_data():
    with session_maker() as session:
        query = select(YamlPath)
        existing_paths = session.execute(query).scalars().all()
        
        if not existing_paths:
            print("Adding initial YAML paths...")
            subsystems = ['main_engine', 'auxiliary_engines']
            for subsystem in subsystems:
                path = f'knowledge_base/{subsystem}'
                yaml_path = YamlPath(subsystem=subsystem, path=path)
                session.add(yaml_path)
            
            session.commit()
            print(f"Added {len(subsystems)} subsystems to the database")
        else:
            print(f"Database already contains {len(existing_paths)} YAML path entries")

if __name__ == '__main__':
    seed_data()