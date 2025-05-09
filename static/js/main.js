document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('query-form');
    const resultsDiv = document.getElementById('results');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const query = document.getElementById('query').value;
        
        fetch('/api/diagnose', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({query: query}),
        })
        .then(response => response.json())
        .then(data => {
            resultsDiv.innerHTML = '<h2>Diagnosis Results</h2>';
            
            if (data.length === 0) {
                resultsDiv.innerHTML += '<p>No matching faults found. Please provide more details.</p>';
            } else {
                data.forEach(result => {
                    resultsDiv.innerHTML += `
                        <div class="result">
                            <h3>${result.fault}</h3>
                            <p>Confidence: ${(result.confidence * 100).toFixed(2)}%</p>
                            <h4>Possible Causes:</h4>
                            <ul>
                                ${result.causes.map(cause => `
                                    <li>
                                        <strong>${cause.name}</strong>
                                        <h5>Checks:</h5>
                                        <ul>
                                            ${cause.checks.map(check => `<li>${check}</li>`).join('')}
                                        </ul>
                                        <h5>Actions:</h5>
                                        <ul>
                                            ${cause.actions.map(action => `<li>${action}</li>`).join('')}
                                        </ul>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    `;
                });
            }
        })
        .catch(error => {
            resultsDiv.innerHTML = `<p>Error: ${error.message}</p>`;
        });
    });
});