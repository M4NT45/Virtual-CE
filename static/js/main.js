document.addEventListener('DOMContentLoaded', function() {
    const queryForm = document.getElementById('query-form');
    const queryInput = document.getElementById('query');
    const chatHistory = document.getElementById('chat-history');
    const engineSelect = document.getElementById('engine-type');
    
    // Auto-resize textarea functionality
    function autoResizeTextarea() {
        // Reset height to auto to get the correct scrollHeight
        this.style.height = 'auto';
        
        // Set the height to the scrollHeight, but limit it between min and max
        const minHeight = 40;
        const maxHeight = 200;
        const newHeight = Math.min(Math.max(this.scrollHeight, minHeight), maxHeight);
        this.style.height = newHeight + 'px';
    }

    // Add event listeners for auto-resize
    queryInput.addEventListener('input', autoResizeTextarea);
    queryInput.addEventListener('change', autoResizeTextarea);
    queryInput.addEventListener('cut', function() {
        setTimeout(autoResizeTextarea.bind(this), 0);
    });
    queryInput.addEventListener('paste', function() {
        setTimeout(autoResizeTextarea.bind(this), 0);
    });

    // Initial resize in case there's default text
    autoResizeTextarea.call(queryInput);
    
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
        
        // Clear input and reset height
        queryInput.value = '';
        queryInput.style.height = '40px'; // Reset to minimum height
        
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
                    flex-wrap: wrap;
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
                
                .custom-clarification {
                    margin-top: 15px;
                    text-align: center;
                }
                
                .custom-clarification input {
                    padding: 8px 12px;
                    border-radius: 4px;
                    border: 1px solid #4a4a6b;
                    background-color: #34344a;
                    color: #e6e6e6;
                    margin-right: 10px;
                    width: 300px;
                    max-width: 60%;
                }
                
                .custom-clarification button {
                    min-width: 80px;
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
        } else if (awaiting === 'component' || awaiting === 'problem') {
            clarificationHtml = `
                <div class="dark-clarification-container">
                    <p>${message}</p>
                    <div class="dark-engine-options">
                        <button class="dark-engine-btn" data-value="Temperature">Temperature</button>
                        <button class="dark-engine-btn" data-value="Pressure">Pressure</button>
                        <button class="dark-engine-btn" data-value="Vibration">Vibration</button>
                        <button class="dark-engine-btn" data-value="Noise">Noise</button>
                        <button class="dark-engine-btn" data-value="Not starting">Not Starting</button>
                        <button class="dark-engine-btn" data-value="Leak">Leak</button>
                    </div>
                    <div class="custom-clarification">
                        <input type="text" id="custom-clarification" placeholder="Or type your specific issue...">
                        <button id="submit-custom-clarification" class="dark-engine-btn">Submit</button>
                    </div>
                </div>`;
        }
        
        // Add clarification request to chat
        addMessage('assistant', clarificationHtml);
        
        // Add event listeners to clarification buttons
        setTimeout(() => {
            document.querySelectorAll('.dark-engine-btn').forEach(button => {
                // Skip the submit button
                if (button.id === 'submit-custom-clarification') {
                    button.addEventListener('click', function() {
                        const customValue = document.getElementById('custom-clarification').value.trim();
                        if (customValue) {
                            submitClarification(customValue, selectedEngine);
                        }
                    });
                    return;
                }
                
                button.addEventListener('click', function() {
                    // Add selected class to the clicked button
                    document.querySelectorAll('.dark-engine-btn').forEach(btn => {
                        if (btn.id !== 'submit-custom-clarification') {
                            btn.classList.remove('selected');
                        }
                    });
                    this.classList.add('selected');
                    
                    const clarificationValue = this.getAttribute('data-value');
                    
                    // Wait a moment to show the selection before submitting
                    setTimeout(() => {
                        submitClarification(clarificationValue, selectedEngine);
                    }, 300);
                });
            });
            
            // Add event listener for Enter key in custom input
            const customInput = document.getElementById('custom-clarification');
            if (customInput) {
                customInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        const customValue = this.value.trim();
                        if (customValue) {
                            submitClarification(customValue, selectedEngine);
                        }
                    }
                });
                // Focus on custom input for better UX
                customInput.focus();
            }
        }, 100);
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
            // Sort causes by probability in descending order (highest probability first)
            const sortedCauses = [...bestMatch.causes].sort((a, b) => b.probability - a.probability);
            
            html += '<p>Potential causes (ranked by probability):</p><ol>';
            sortedCauses.forEach((cause, index) => {
                const percentage = Math.round(cause.probability * 100);
                // Add priority class based on probability
                const priorityClass = percentage >= 80 ? 'high-priority' : 
                                     percentage >= 50 ? 'medium-priority' : 'low-priority';
                
                html += `
                    <li>
                        <div class="cause ${priorityClass}">
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
    
    // Create and add reset conversation button
    const resetButton = document.createElement('button');
    resetButton.textContent = 'Reset Conversation';
    resetButton.className = 'reset-button';
    resetButton.addEventListener('click', function() {
        if (confirm('Are you sure you want to reset the conversation?')) {
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
                // Reset textarea height
                queryInput.style.height = '40px';
                queryInput.focus();
            })
            .catch(error => {
                console.error('Error resetting conversation:', error);
                addMessage('assistant', 'Sorry, I couldn\'t reset the conversation. Please try again.');
            });
        }
    });
    
    // Append reset button to body for fixed positioning
    document.body.appendChild(resetButton);
    
    // Add initial welcome message
    addMessage('assistant', 'Welcome to Virtual Chief Engineer! I can help you diagnose marine machinery issues. Please describe the problem you\'re experiencing.');
    
    // Focus on input field
    queryInput.focus();
});