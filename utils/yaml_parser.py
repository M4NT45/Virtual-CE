import re
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
            
        for filename in os.listdir(base_path):
            if filename.endswith('.yaml'):
                file_path = os.path.join(base_path, filename)
                
                with open(file_path, 'r') as file:
                    content = file.read()
                
                fault_sections = re.split(r'## Fault \d+', content)
                if len(fault_sections) <= 1:
                    try:
                        fault_data = yaml.safe_load(content)
                        if 'fault' in fault_data and fault_data['fault'].get('name') == fault_name:
                            return fault_data
                    except yaml.YAMLError:
                        continue
                else:
                    for section in fault_sections[1:]:
                        try:
                            section_data = yaml.safe_load('fault:' + section)
                            if section_data and 'fault' in section_data and section_data['fault'].get('name') == fault_name:
                                return section_data
                        except yaml.YAMLError:
                            continue
        
        return None
    
    def get_all_faults(self, subsystem=None, file_filters=None):
        results = []
        
        if subsystem:
            subsystems = [subsystem]
        else:
            subsystems = self.yaml_paths.keys()
            
        for sys in subsystems:
            base_path = self.yaml_paths.get(sys)
            if not base_path or not os.path.exists(base_path):
                continue
            
            all_files = [f for f in os.listdir(base_path) if f.endswith('.yaml')]
            
            if file_filters:
                filtered_files = []
                for pattern in file_filters:
                    regex_pattern = pattern.replace('.', r'\.').replace('*', '.*')
                    for file in all_files:
                        if re.match(regex_pattern, file) and file not in filtered_files:
                            filtered_files.append(file)
                files_to_process = filtered_files
            else:
                files_to_process = all_files
                
            for filename in files_to_process:
                file_path = os.path.join(base_path, filename)
                
                try:
                    with open(file_path, 'r') as file:
                        content = file.read()
                    
                    if '## Fault' in content:
                        fault_sections = re.split(r'## Fault \d+', content)
                        
                        for i, section in enumerate(fault_sections[1:], 1):
                            try:
                                if not section.strip().startswith('fault:'):
                                    section = 'fault:' + section
                                
                                fault_data = yaml.safe_load(section)
                                if fault_data and 'fault' in fault_data:
                                    fault_data['_source_file'] = filename
                                    fault_data['_fault_number'] = i
                                    fault_data['_subsystem'] = sys
                                    results.append(fault_data)
                            except yaml.YAMLError:
                                pass
                    else:
                        try:
                            fault_data = yaml.safe_load(content)
                            if fault_data and 'fault' in fault_data:
                                fault_data['_source_file'] = filename
                                fault_data['_fault_number'] = 1
                                fault_data['_subsystem'] = sys
                                results.append(fault_data)
                        except yaml.YAMLError:
                            pass
                except Exception:
                    pass
        
        return results