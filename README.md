Project Proposal: Virtual Chief Engineer
Project Title:
Virtual Chief Engineer - Web-Based Hybrid Fault Diagnosis Assistant for Marine Machinery
Objective:
To develop a web-based intelligent assistant that helps marine engineers diagnose and troubleshoot
machinery faults. The system will combine rule-based expert logic with a lightweight neural model to deliver
reliable and flexible responses to technical issues in natural language.
Project Description:
The assistant will allow users (marine engineers or cadets) to input machinery symptoms or descriptions of
problems through a simple HTML interface. It will then analyze the input using two reasoning layers:
1. Rule-Based Reasoning:
A structured set of fault trees and decision rules created from real-world marine engineering experience
and technical manuals. These rules will map common symptoms to likely causes and suggested checks or
actions.
2. Neural Semantic Matching:
A compact transformer-based language model (e.g. MiniLM or DistilBERT) will be used to understand
fuzzy, imprecise, or non-standard phrasing. The model will compare user input to a library of fault cases
using semantic similarity.
The combination ensures high performance for well-known problems and greater flexibility for less structured
inputs.
Scope (Minimum Viable Product):
- Interface: HTML/JS-based front-end with a Flask or FastAPI backend for processing.
Project Proposal: Virtual Chief Engineer
- Knowledge Base: Include at least 50-100 fault cases across multiple marine subsystems, such as:
- Main engine
- Purifier
- Fuel system
- Air compressors
- Pumps and coolers
- Logic Engine: Implement a hybrid engine that uses rules first, then backs up with neural similarity when
needed.
- Output: Display suggested causes and actions with confidence or priority levels.
Technologies Used:
- Frontend: HTML, CSS, JavaScript
- Backend: Python (Flask or FastAPI)
- Data Storage: YAML or JSON (for rule-based logic and fault case database)
- NLP Model: SentenceTransformers (MiniLM or DistilBERT)
- Other Tools: Git, virtualenv, VS Code, HuggingFace Transformers
Expected Outcome:
A web-accessible prototype assistant that can understand and respond to engineering issues in natural
language. It will support both standard and non-standard phrasing, combining deterministic and intelligent
behavior to simulate a virtual "chief engineer."
