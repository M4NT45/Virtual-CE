document.addEventListener('DOMContentLoaded', function() {
    const queryForm = document.getElementById('query-form');
    const queryInput = document.getElementById('query');
    const chatHistory = document.getElementById('chat-history');
    const submitBtn = document.getElementById('submit-btn');

    // Auto-resize textarea as user types
    queryInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        // Reset to default height if empty
        if (this.value === '') {
            this.style.height = '';
        }
    });

    // Handle form submission
    queryForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const query = queryInput.value.trim();
        
        if (query === '') return;
        
        // Add user message to chat
        addMessage(query, 'user');
        
        // Clear input
        queryInput.value = '';
        queryInput.style.height = '';
        
        // Show loading indicator
        const loadingMessage = addLoadingMessage();
        
        // Disable submit button while processing
        submitBtn.disabled = true;
        
        // Send query to backend
        fetchDiagnosis(query)
            .then(response => {
                // Remove loading message
                loadingMessage.remove();
                
                // Add response to chat
                addDiagnosisMessage(response);
            })
            .catch(error => {
                // Remove loading message
                loadingMessage.remove();
                
                // Add error message
                addErrorMessage('Sorry, there was an error processing your query. Please try again.');
                console.error('Error:', error);
            })
            .finally(() => {
                // Re-enable submit button
                submitBtn.disabled = false;
                
                // Scroll to bottom
                scrollToBottom();
            });
    });

    // Function to add messages to the chat
    function addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = `<p>${content}</p>`;
        
        messageDiv.appendChild(messageContent);
        chatHistory.appendChild(messageDiv);
        
        scrollToBottom();
        return messageDiv;
    }

    // Function to add loading indicator
    function addLoadingMessage() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant';
        
        const loadingContent = document.createElement('div');
        loadingContent.className = 'loading';
        
        // Add three loading dots
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'loading-dot';
            loadingContent.appendChild(dot);
        }
        
        loadingDiv.appendChild(loadingContent);
        chatHistory.appendChild(loadingDiv);
        
        scrollToBottom();
        return loadingDiv;
    }

    // Function to add error message
    function addErrorMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = `<p style="color: var(--error-color);">${message}</p>`;
        
        messageDiv.appendChild(messageContent);
        chatHistory.appendChild(messageDiv);
        
        scrollToBottom();
        return messageDiv;
    }

    // Function to add diagnosis response
    function addDiagnosisMessage(diagnosis) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Format the diagnostic response
        let html = '';
        
        if (diagnosis.error) {
            html = `<p>${diagnosis.error}</p>`;
        } else {
            // Calculate confidence percentage
            const confidencePercent = Math.round(diagnosis.confidence * 100);
            const confidenceClass = confidencePercent > 80 ? 'success-color' : 
                                   confidencePercent > 50 ? 'accent-color' : 'error-color';
            
            html = `
                <h3>${diagnosis.fault}</h3>
                <p class="confidence">Confidence: <span style="color: var(--${confidenceClass});">${confidencePercent}%</span></p>
                <div class="fault-item">
                    <h4>Symptoms</h4>
                    <ul>
                        ${diagnosis.symptoms.map(symptom => `<li>${symptom}</li>`).join('')}
                    </ul>
                </div>
            `;
            
            // Add causes section
            html += `<div class="diagnosis-details">`;
            
            diagnosis.causes.forEach(cause => {
                const probability = Math.round(cause.probability * 100);
                
                html += `
                    <div class="fault-item">
                        <h4>${cause.name} (${probability}% probability)</h4>
                        <div class="checks-actions">
                            <div>
                                <h5>Checks to perform:</h5>
                                <ul>
                                    ${cause.checks.map(check => `<li>${check}</li>`).join('')}
                                </ul>
                            </div>
                            <div>
                                <h5>Recommended actions:</h5>
                                <ul>
                                    ${cause.actions.map(action => `<li>${action}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `</div>`;
        }
        
        messageContent.innerHTML = html;
        messageDiv.appendChild(messageContent);
        chatHistory.appendChild(messageDiv);
        
        scrollToBottom();
        return messageDiv;
    }

    // Function to scroll chat to bottom
    function scrollToBottom() {
        const chatContainer = document.querySelector('.chat-container');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Function to fetch diagnosis from backend
    async function fetchDiagnosis(query) {
        const response = await fetch('/diagnose', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `query=${encodeURIComponent(query)}`
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
});