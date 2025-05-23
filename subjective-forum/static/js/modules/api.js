/**
 * API Module
 * 
 * Handles all API communication with the server.
 */

/**
 * Save a question answer to the server
 * @param {string} questionId - The ID of the question
 * @param {Object} answers - Object containing metric ratings
 * @param {number} timeSpent - Time spent on the question in seconds
 * @returns {Promise} - Promise that resolves with the server response
 */
export function saveAnswer(questionId, answers, timeSpent) {
    return fetch('/api/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            questionId,
            answers,
            timeSpent
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    });
}

/**
 * Finish the test and save all results
 * @returns {Promise} - Promise that resolves with the server response
 */
export function finishTest() {
    return fetch('/api/finish', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    });
}

/**
 * Send a heartbeat to keep the session alive
 * @returns {Promise} - Promise that resolves with the server response
 */
export function sendHeartbeat() {
    return fetch('/api/heartbeat')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        });
}

/**
 * Get a list of available audio files for a prompt
 * @param {string} promptId - The ID of the prompt
 * @returns {Promise} - Promise that resolves with the list of audio files
 */
export function getAudioFiles(promptId) {
    return fetch(`/api/audio/list/${promptId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        });
}

/**
 * Set up automatic heartbeat to keep session alive
 * @param {number} interval - Interval in milliseconds (default: 60000 = 1 minute)
 * @returns {number} - The interval ID for clearing if needed
 */
export function setupHeartbeat(interval = 60000) {
    return setInterval(() => {
        sendHeartbeat().catch(error => {
            console.error('Heartbeat error:', error);
        });
    }, interval);
}