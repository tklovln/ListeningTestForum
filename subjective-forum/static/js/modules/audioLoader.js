/**
 * Audio Loader Module
 * 
 * Handles preloading and caching of audio files for smooth playback experience.
 */

/**
 * AudioLoader class for managing audio preloading and caching
 */
export class AudioLoader {
    /**
     * Create a new AudioLoader instance
     * @param {string} audioRoot - The root path for audio files
     */
    constructor(audioRoot) {
        this.audioRoot = audioRoot;
        this.audioContext = null;
        this.loadedAudio = new Map();
        this.loadPromises = new Map();
        this.initAudioContext();
    }

    /**
     * Initialize the Web Audio API context
     */
    initAudioContext() {
        try {
            // Create audio context
            window.AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioContext = new AudioContext();
            
            // Handle iOS/Safari autoplay policy
            this.unlockAudioContext();
        } catch (e) {
            console.error('Web Audio API not supported:', e);
        }
    }

    /**
     * Unlock audio context on first user interaction (for mobile browsers)
     */
    unlockAudioContext() {
        const unlockEvents = ['touchstart', 'touchend', 'mousedown', 'keydown'];
        
        const unlock = () => {
            if (this.audioContext && this.audioContext.state === 'suspended') {
                this.audioContext.resume();
            }
            
            // Remove event listeners once unlocked
            unlockEvents.forEach(event => {
                document.removeEventListener(event, unlock);
            });
        };
        
        // Add event listeners for user interaction
        unlockEvents.forEach(event => {
            document.addEventListener(event, unlock, { once: true });
        });
    }

    /**
     * Preload a list of audio files
     * @param {string} promptId - The prompt ID
     * @param {Array<string>} models - List of model tags to preload
     * @param {Function} onProgress - Progress callback function
     * @returns {Promise} - Promise that resolves when all files are loaded
     */
    preloadAudioFiles(promptId, models, onProgress = null) {
        const filesToLoad = ['prompt', ...models];
        const totalFiles = filesToLoad.length;
        let loadedFiles = 0;
        
        // Create array of promises for each file
        const loadPromises = filesToLoad.map(tag => {
            const url = `${this.audioRoot}/${promptId}_${tag}.mp3`;
            return this.loadAudio(url).then(() => {
                loadedFiles++;
                if (onProgress) {
                    onProgress(loadedFiles / totalFiles);
                }
            });
        });
        
        return Promise.all(loadPromises);
    }

    /**
     * Load a single audio file
     * @param {string} url - URL of the audio file to load
     * @returns {Promise} - Promise that resolves when the file is loaded
     */
    loadAudio(url) {
        // Return existing promise if already loading
        if (this.loadPromises.has(url)) {
            return this.loadPromises.get(url);
        }
        
        // Return cached audio if already loaded
        if (this.loadedAudio.has(url)) {
            return Promise.resolve(this.loadedAudio.get(url));
        }
        
        // Create new load promise
        const loadPromise = new Promise((resolve, reject) => {
            // Try to use Cache API first
            if ('caches' in window) {
                caches.open('audio-cache').then(cache => {
                    // Check if already in cache
                    cache.match(url).then(response => {
                        if (response) {
                            // File is in cache, load it
                            this.processAudioFile(response, url).then(resolve).catch(reject);
                        } else {
                            // File not in cache, fetch it
                            fetch(url)
                                .then(response => {
                                    // Clone the response to store in cache
                                    const clonedResponse = response.clone();
                                    cache.put(url, clonedResponse);
                                    
                                    // Process the audio file
                                    this.processAudioFile(response, url).then(resolve).catch(reject);
                                })
                                .catch(reject);
                        }
                    });
                }).catch(() => {
                    // Cache API failed, fallback to regular fetch
                    this.fetchAndProcessAudio(url).then(resolve).catch(reject);
                });
            } else {
                // Cache API not supported, fallback to regular fetch
                this.fetchAndProcessAudio(url).then(resolve).catch(reject);
            }
        });
        
        // Store the promise
        this.loadPromises.set(url, loadPromise);
        
        return loadPromise;
    }

    /**
     * Fetch and process an audio file
     * @param {string} url - URL of the audio file
     * @returns {Promise} - Promise that resolves when the file is processed
     */
    fetchAndProcessAudio(url) {
        return fetch(url)
            .then(response => this.processAudioFile(response, url));
    }

    /**
     * Process an audio file from fetch response
     * @param {Response} response - Fetch response object
     * @param {string} url - URL of the audio file
     * @returns {Promise} - Promise that resolves when the file is processed
     */
    processAudioFile(response, url) {
        return response.arrayBuffer()
            .then(arrayBuffer => {
                // If Web Audio API is available, decode the audio
                if (this.audioContext) {
                    return this.audioContext.decodeAudioData(arrayBuffer)
                        .then(audioBuffer => {
                            // Store the decoded audio buffer
                            this.loadedAudio.set(url, audioBuffer);
                            return audioBuffer;
                        });
                } else {
                    // Web Audio API not available, store the raw array buffer
                    this.loadedAudio.set(url, arrayBuffer);
                    return arrayBuffer;
                }
            });
    }

    /**
     * Get a loaded audio file
     * @param {string} url - URL of the audio file
     * @returns {AudioBuffer|ArrayBuffer|null} - The loaded audio data or null if not loaded
     */
    getAudio(url) {
        return this.loadedAudio.get(url) || null;
    }

    /**
     * Check if an audio file is loaded
     * @param {string} url - URL of the audio file
     * @returns {boolean} - True if the file is loaded
     */
    isLoaded(url) {
        return this.loadedAudio.has(url);
    }

    /**
     * Create an audio element with the loaded audio
     * @param {string} url - URL of the audio file
     * @returns {HTMLAudioElement|null} - Audio element or null if not loaded
     */
    createAudioElement(url) {
        if (!this.isLoaded(url)) {
            return null;
        }
        
        const audio = new Audio();
        
        // If we have a decoded audio buffer, create an object URL
        const audioData = this.getAudio(url);
        if (audioData instanceof AudioBuffer) {
            // Create a blob from the audio buffer
            const wav = this.audioBufferToWav(audioData);
            const blob = new Blob([wav], { type: 'audio/wav' });
            audio.src = URL.createObjectURL(blob);
        } else {
            // Use the original URL
            audio.src = url;
        }
        
        return audio;
    }

    /**
     * Convert an AudioBuffer to WAV format
     * @param {AudioBuffer} audioBuffer - The audio buffer to convert
     * @returns {ArrayBuffer} - WAV file as array buffer
     */
    audioBufferToWav(audioBuffer) {
        // Implementation of audioBufferToWav would go here
        // This is a simplified placeholder - in a real implementation,
        // you would convert the AudioBuffer to a WAV file format
        
        // For now, we'll just return a simple buffer
        return new ArrayBuffer(0);
    }
}

// Create and export a singleton instance
const audioLoader = new AudioLoader('/static/audio');
export default audioLoader;