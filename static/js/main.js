document.addEventListener('DOMContentLoaded', function() {
    const queryForm = document.getElementById('query-form');
    const queryInput = document.getElementById('query');
    const chatHistory = document.getElementById('chat-history');
    const engineSelect = document.getElementById('engine-type');
    
    // Update tooltip text based on selected engine
    engineSelect.addEventListener('change', function() {
        const engineTooltip = document.querySelector('.engine-tooltip');
        const selectedEngine = engineSelect.value;
        
        if (selectedEngine === 'rule') {
            engineTooltip.textContent = 'Uses structured fault trees and decision rules for precise diagnosis';
        } else if (selectedEngine === 'neural') {
            engineTooltip.textContent = 'Uses semantic similarity to understand natural language descriptions';
        } else { // hybrid
            engineTooltip.textContent = 'Combines rule-based knowledge with neural semantic understanding for best results';
        }
    });
    
    queryForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const userQuery = queryInput.value.trim();
        if (!userQuery) return;
        
        // Add user message to chat
        addMessage('user', userQuery);
        
        // Clear input
        queryInput.value = '';
        
        // Get selected engine
        const selectedEngine = engineSelect.value;
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send query to backend with selected engine
        fetch('/api/diagnose', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: userQuery,
                engine: selectedEngine
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Check if this is a clarification request
            if (data.type === 'clarification') {
                handleClarificationRequest(data, selectedEngine);
            } else {
                // Format and display regular diagnosis response
                const formattedResponse = formatDiagnosisResponse(data, selectedEngine);
                addMessage('assistant', formattedResponse);
            }
            
            // Scroll to bottom
            chatHistory.scrollTop = chatHistory.scrollHeight;
        })
        .catch(error => {
            console.error('Error:', error);
            hideTypingIndicator();
            addMessage('assistant', 'Sorry, I encountered an error processing your request.');
        });
    });
    
    // Handle clarification requests
    function handleClarificationRequest(data, selectedEngine) {
        const awaiting = data.awaiting;
        const message = data.message;
        
        // Add dark theme styling to the document if not already present
        if (!document.getElementById('dark-theme-styles')) {
            const darkThemeStyles = document.createElement('style');
            darkThemeStyles.id = 'dark-theme-styles';
            darkThemeStyles.textContent = `
                .dark-clarification-container {
                    background-color: #242444;
                    border-radius: 10px;
                    padding: 20px;
                    color: #e6e6e6;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                }
                
                .dark-clarification-container p {
                    color: #a0a0a0;
                    margin-bottom: 15px;
                    text-align: center;
                }
                
                .dark-engine-options {
                    display: flex;
                    justify-content: center;
                    gap: 15px;
                    margin: 15px 0;
                }
                
                .dark-engine-btn {
                    background-color: #34344a;
                    color: #e6e6e6;
                    border: none;
                    border-radius: 5px;
                    padding: 12px 24px;
                    font-size: 14px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    min-width: 150px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
                }
                
                .dark-engine-btn:hover {
                    background-color: #4a4a6b;
                }
                
                .dark-engine-btn.selected {
                    background-color: #3d56b2;
                }
            `;
            document.head.appendChild(darkThemeStyles);
        }
        
        let clarificationHtml = '';
        
        // Add appropriate options based on what we're clarifying
        if (awaiting === 'engine') {
            clarificationHtml = `
                <div class="dark-clarification-container">
                    <p>${message}</p>
                    <div class="dark-engine-options">
                        <button class="dark-engine-btn" data-value="Main Engine">Main Engine</button>
                        <button class="dark-engine-btn" data-value="Auxiliary Engine">Auxiliary Engine</button>
                    </div>
                </div>`;
        } else if (awaiting === 'component') {
            clarificationHtml = `
                <div class="clarification-request">
                    <p>${message}</p>
                    <div class="clarification-options component-options">
                        <button class="clarification-btn" data-value="Temperature">Temperature</button>
                        <button class="clarification-btn" data-value="Pressure">Pressure</button>
                        <button class="clarification-btn" data-value="Vibration">Vibration</button>
                        <button class="clarification-btn" data-value="Noise">Noise</button>
                        <button class="clarification-btn" data-value="Not starting">Not Starting</button>
                        <button class="clarification-btn" data-value="Leak">Leak</button>
                    </div>
                    <div class="custom-clarification">
                        <input type="text" id="custom-clarification" placeholder="Or type your response...">
                        <button id="submit-custom-clarification">Submit</button>
                    </div>
                </div>`;
        }
        
        // Add clarification request to chat
        addMessage('assistant', clarificationHtml);
        
        // Add event listeners to clarification buttons
        if (awaiting === 'engine') {
            document.querySelectorAll('.dark-engine-btn').forEach(button => {
                button.addEventListener('click', function() {
                    // Add selected class to the clicked button
                    document.querySelectorAll('.dark-engine-btn').forEach(btn => {
                        btn.classList.remove('selected');
                    });
                    this.classList.add('selected');
                    
                    const clarificationValue = this.getAttribute('data-value');
                    
                    // Wait a moment to show the selection before submitting
                    setTimeout(() => {
                        submitClarification(clarificationValue, selectedEngine);
                    }, 300);
                });
            });
        } else {
            document.querySelectorAll('.clarification-btn').forEach(button => {
                button.addEventListener('click', function() {
                    const clarificationValue = this.getAttribute('data-value');
                    submitClarification(clarificationValue, selectedEngine);
                });
            });
            
            // Add event listener to custom clarification button
            document.getElementById('submit-custom-clarification').addEventListener('click', function() {
                const customValue = document.getElementById('custom-clarification').value.trim();
                if (customValue) {
                    submitClarification(customValue, selectedEngine);
                }
            });
            
            // Also allow Enter key in the custom input
            document.getElementById('custom-clarification').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    const customValue = this.value.trim();
                    if (customValue) {
                        submitClarification(customValue, selectedEngine);
                    }
                }
            });
        }
    }
    
    // Submit clarification response
    function submitClarification(clarificationValue, selectedEngine) {
        // Add user clarification to chat
        addMessage('user', clarificationValue);
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send clarification to backend
        fetch('/api/diagnose', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: clarificationValue,
                engine: selectedEngine
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide typing indicator
            hideTypingIndicator();
            
            // Check if we need more clarification
            if (data.type === 'clarification') {
                handleClarificationRequest(data, selectedEngine);
            } else {
                // Format and display diagnosis response
                const formattedResponse = formatDiagnosisResponse(data, selectedEngine);
                addMessage('assistant', formattedResponse);
            }
            
            // Scroll to bottom
            chatHistory.scrollTop = chatHistory.scrollHeight;
        })
        .catch(error => {
            console.error('Error:', error);
            hideTypingIndicator();
            addMessage('assistant', 'Sorry, I encountered an error processing your clarification.');
        });
    }
    
    // Add typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing';
        typingDiv.innerHTML = '<div class="message-content"><div class="typing-indicator"><span></span><span></span><span></span></div></div>';
        chatHistory.appendChild(typingDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    // Remove typing indicator
    function hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Add message to chat
    function addMessage(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    // Format diagnosis response
    function formatDiagnosisResponse(data, engineType) {
        // Check if data is an array and get the best match (highest confidence)
        const bestMatch = Array.isArray(data) && data.length > 0 ? data[0] : data;
        
        // Customize based on your data structure
        let engineLabel = '';
        if (engineType === 'rule') {
            engineLabel = '<span class="engine-label rule">Rule-Based Analysis</span>';
        } else if (engineType === 'neural') {
            engineLabel = '<span class="engine-label neural">Neural Analysis</span>';
        } else {
            engineLabel = '<span class="engine-label hybrid">Hybrid Analysis</span>';
        }
        
        // Add enhanced query information if available
        let queryInfo = '';
        if (data.original_query && data.enhanced_query && data.original_query !== data.enhanced_query) {
            queryInfo = `
                <div class="query-info">
                    <p><strong>I understood your query as:</strong> ${data.enhanced_query}</p>
                </div>`;
        }
        
        let html = `<p>${engineLabel} ${queryInfo} Based on your description, I've identified the following issue:</p>`;
        
        if (bestMatch && bestMatch.fault) {
            html += `<h3>${bestMatch.fault}</h3>`;
        }
        
        if (bestMatch && bestMatch.causes && bestMatch.causes.length > 0) {
            html += '<p>Potential causes (ranked by probability):</p><ol>';
            bestMatch.causes.forEach(cause => {
                const percentage = Math.round(cause.probability * 100);
                html += `
                    <li>
                        <div class="cause">
                            <h4>${cause.name} <span class="probability">${percentage}%</span></h4>
                            <div class="cause-details">
                                <div class="checks">
                                    <h5>Recommended Checks:</h5>
                                    <ul>
                                        ${cause.checks.map(check => `<li>${check}</li>`).join('')}
                                    </ul>
                                </div>
                                <div class="actions">
                                    <h5>Recommended Actions:</h5>
                                    <ul>
                                        ${cause.actions.map(action => `<li>${action}</li>`).join('')}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </li>`;
            });
            html += '</ol>';
        } else {
            html += '<p>I couldn\'t identify specific causes for this issue. Please provide more details or try a different description.</p>';
        }
        
        return html;
    }
    
    // Add a reset conversation button (optional)
    const resetButton = document.createElement('button');
    resetButton.textContent = 'Reset Conversation';
    resetButton.className = 'reset-button';
    resetButton.addEventListener('click', function() {
        fetch('/api/reset_conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(() => {
            // Clear chat history
            chatHistory.innerHTML = '';
            addMessage('assistant', 'Conversation has been reset. How can I help you with marine machinery diagnosis?');
        });
    });
    document.querySelector('.chat-container').appendChild(resetButton);
});