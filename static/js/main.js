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
            
            // Format and display response
            const formattedResponse = formatDiagnosisResponse(data, selectedEngine);
            addMessage('assistant', formattedResponse);
            
            // Scroll to bottom
            chatHistory.scrollTop = chatHistory.scrollHeight;
        })
        .catch(error => {
            console.error('Error:', error);
            hideTypingIndicator();
            addMessage('assistant', 'Sorry, I encountered an error processing your request.');
        });
    });
    
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
        
        let html = `<p>${engineLabel} Based on your description, I've identified the following issue:</p>`;
        
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
});