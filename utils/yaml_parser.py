import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
            
        # Search through all YAML files in the directory to find the specified fault
        for filename in os.listdir(base_path):
            if filename.endswith('.yaml'):
                file_path = os.path.join(base_path, filename)
                
                # Read the content of the file as text first
                with open(file_path, 'r') as file:
                    content = file.read()
                
                # Split the content into individual fault sections
                fault_sections = re.split(r'## Fault \d+', content)
                if len(fault_sections) <= 1:  # No fault sections or single section without header
                    # Try to parse the whole file as a single fault
                    try:
                        fault_data = yaml.safe_load(content)
                        if 'fault' in fault_data and fault_data['fault'].get('name') == fault_name:
                            return fault_data
                    except yaml.YAMLError:
                        continue
                else:
                    # Process each fault section
                    for section in fault_sections[1:]:  # Skip the first section which is before the first fault header
                        try:
                            section_data = yaml.safe_load('fault:' + section)
                            if section_data and 'fault' in section_data and section_data['fault'].get('name') == fault_name:
                                return section_data
                        except yaml.YAMLError:
                            continue
        
        return None
    
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
                    file_path = os.path.join(base_path, filename)
                    
                    try:
                        # First try to read the file as a normal YAML file
                        with open(file_path, 'r') as file:
                            content = file.read()
                        
                        # Check if the file contains multiple fault sections
                        if '## Fault' in content:
                            # Split the content based on fault headers
                            fault_sections = re.split(r'## Fault \d+', content)
                            
                            # Process each fault section
                            for i, section in enumerate(fault_sections[1:], 1):  # Skip the first split which is before any fault
                                try:
                                    # Add the fault: prefix back if needed
                                    if not section.strip().startswith('fault:'):
                                        section = 'fault:' + section
                                    
                                    fault_data = yaml.safe_load(section)
                                    if fault_data and 'fault' in fault_data:
                                        # Add source information
                                        fault_data['_source_file'] = filename
                                        fault_data['_fault_number'] = i
                                        results.append(fault_data)
                                except yaml.YAMLError as e:
                                    print(f"Error parsing fault section {i} in {filename}: {e}")
                        else:
                            # Try to parse the file as a single fault
                            try:
                                fault_data = yaml.safe_load(content)
                                if fault_data and 'fault' in fault_data:
                                    # Add source information
                                    fault_data['_source_file'] = filename
                                    fault_data['_fault_number'] = 1
                                    results.append(fault_data)
                            except yaml.YAMLError as e:
                                print(f"Error parsing file {filename}: {e}")
                    except Exception as e:
                        print(f"Error processing file {filename}: {e}")
        
        return results