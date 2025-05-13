import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import yaml
from sqlalchemy import select
from models.yaml_path_class import YamlPath

class YamlReader:
    def __init__(self, session):
        self.yaml_paths = {}
        self.session = session
        self._load_paths_from_db()
        
    def _load_paths_from_db(self):
        query = select(YamlPath)
        paths = self.session.execute(query).scalars().all()
        
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