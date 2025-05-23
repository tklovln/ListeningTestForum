// Story controller
document.addEventListener('DOMContentLoaded', function() {
    // Get data from HTML attributes
    const storyContainer = document.querySelector('.story-container');
    const QUESTION_ID = storyContainer.getAttribute('data-question-id');
    const PROMPT_ID = storyContainer.getAttribute('data-prompt-id');
    
    // Add error handling for JSON parsing
    let MODELS = [];
    try {
        const modelsData = storyContainer.getAttribute('data-models');
        console.log('Models data:', modelsData);
        MODELS = modelsData ? JSON.parse(modelsData) : [];
        console.log('Parsed MODELS:', MODELS);
        
        // If MODELS is still empty, use hardcoded values from config
        if (MODELS.length === 0) {
            console.warn('Models array is empty, using hardcoded values');
            MODELS = ["gt", "methodA", "methodB"];
        }
    } catch (e) {
        console.error('Error parsing models data:', e);
        // Fallback to hardcoded values
        MODELS = ["gt", "methodA", "methodB"];
    }
    
    let METRICS = [];
    try {
        const metricsData = storyContainer.getAttribute('data-metrics');
        console.log('Metrics data:', metricsData);
        METRICS = metricsData ? JSON.parse(metricsData) : [];
    } catch (e) {
        console.error('Error parsing metrics data:', e);
    }
    
    const IS_LAST = storyContainer.getAttribute('data-is-last') === 'true';
    const NEXT_URL = storyContainer.getAttribute('data-next-url');
    const PREV_URL = storyContainer.getAttribute('data-prev-url');
    const AUDIO_ROOT = storyContainer.getAttribute('data-audio-root');
    
    // Elements
    const storyElement = document.getElementById('story');
    const progressSegments = document.getElementById('progress-segments');
    const navLeft = document.getElementById('nav-left');
    const navRight = document.getElementById('nav-right');
    const loadingIndicator = document.getElementById('loading-indicator');
    const prevButton = document.getElementById('prev-button');
    const nextButton = document.getElementById('next-button');
    
    // State
    let currentPage = 0;
    const totalPages = 2 + MODELS.length; // Prompt + Models + Rating
    console.log(`Total pages: ${totalPages} (1 prompt page + ${MODELS.length} model pages + 1 summary page)`);
    let startTime = Date.now();
    let answers = {};
    let audioElements = {};
    let audioLoaded = {};
    
    // Initialize progress bar
    for (let i = 0; i < totalPages; i++) {
        const segment = document.createElement('div');
        segment.className = 'progress-segment';
        if (i === 0) segment.classList.add('active');
        progressSegments.appendChild(segment);
    }
    
    // Initialize audio elements
    function initAudio() {
        console.log('Initializing audio elements');
        
        // Prompt audio
        const promptAudio = document.getElementById('prompt-audio');
        const promptSrc = promptAudio.dataset.src;
        console.log('Setting prompt audio src:', promptSrc);
        promptAudio.src = promptSrc;
        
        // Add event listeners for debugging
        promptAudio.addEventListener('canplaythrough', () => {
            console.log('Prompt audio can play through');
        });
        
        promptAudio.addEventListener('error', (e) => {
            console.error('Prompt audio error:', e);
        });
        
        audioElements['prompt'] = promptAudio;
        
        // Model audios
        MODELS.forEach(model => {
            const modelAudio = document.getElementById(`model-${model}-audio`);
            const modelSrc = modelAudio.dataset.src;
            console.log(`Setting ${model} audio src:`, modelSrc);
            modelAudio.src = modelSrc;
            
            // Add event listeners for debugging
            modelAudio.addEventListener('canplaythrough', () => {
                console.log(`${model} audio can play through`);
            });
            
            modelAudio.addEventListener('error', (e) => {
                console.error(`${model} audio error:`, e);
            });
            
            audioElements[model] = modelAudio;
        });
        
        // Preload all audio files
        preloadAudio();
    }
    
    // Preload audio files
    async function preloadAudio() {
        try {
            // Check if Cache API is available
            if ('caches' in window) {
                const cache = await caches.open('audio-cache');
                
                // Preload prompt audio
                const promptUrl = `${window.location.origin}/api/audio/${PROMPT_ID}_prompt.mp3`;
                console.log('Preloading prompt audio from URL:', promptUrl);
                
                // Use fetch instead of cache.add for better error handling
                fetch(promptUrl)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                        return cache.put(promptUrl, response);
                    })
                    .then(() => {
                        console.log('Prompt audio cached successfully');
                        audioLoaded['prompt'] = true;
                    })
                    .catch(err => {
                        console.error('Error caching prompt audio:', err);
                    });
                
                // Preload model audios
                MODELS.forEach(model => {
                    const modelUrl = `${window.location.origin}/api/audio/${PROMPT_ID}_${model}.mp3`;
                    console.log(`Preloading ${model} audio from URL:`, modelUrl);
                    
                    // Use fetch instead of cache.add for better error handling
                    fetch(modelUrl)
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP error! Status: ${response.status}`);
                            }
                            return cache.put(modelUrl, response);
                        })
                        .then(() => {
                            console.log(`${model} audio cached successfully`);
                            audioLoaded[model] = true;
                        })
                        .catch(err => {
                            console.error(`Error caching model audio (${model}):`, err);
                        });
                });
            }
        } catch (error) {
            console.error('Error preloading audio:', error);
        }
    }
    
    // Navigate to a specific page
    function goToPage(pageIndex) {
        if (pageIndex < 0 || pageIndex >= totalPages) return;
        
        // Update current page
        currentPage = pageIndex;
        
        // Scroll to the page
        const storyPages = document.querySelectorAll('.story-page');
        storyPages[pageIndex].scrollIntoView({ behavior: 'smooth' });
        
        // Update progress bar
        const segments = document.querySelectorAll('.progress-segment');
        segments.forEach((segment, i) => {
            segment.classList.toggle('active', i <= pageIndex);
        });
        
        // Ensure audio plays immediately when the page is shown
        // (not just when the user taps)
        console.log(`Going to page ${pageIndex}, will play audio automatically`);
        setTimeout(() => {
            playAudioForCurrentPage();
        }, 300);
    }
    
    // Function to play audio for the current page
    function playAudioForCurrentPage() {
        console.log(`Playing audio for page ${currentPage}, total pages: ${totalPages}`);
        console.log('Available models:', MODELS);
        console.log('Available audio elements:', Object.keys(audioElements));
        
        // Stop all audio playback first
        Object.values(audioElements).forEach(audio => {
            if (audio) {
                audio.pause();
                audio.currentTime = 0;
            }
        });
        
        if (currentPage === 0) {
            // Prompt page
            const promptAudio = audioElements['prompt'];
            const progressElement = document.getElementById('prompt-progress');
            const statusElement = document.getElementById('prompt-status');
            
            if (promptAudio) {
                console.log('Playing prompt audio automatically');
                
                // Set up progress tracking if not already set
                if (!promptAudio._hasProgressListener) {
                    promptAudio.addEventListener('timeupdate', () => {
                        if (promptAudio.duration) {
                            const percent = (promptAudio.currentTime / promptAudio.duration) * 100;
                            if (progressElement) progressElement.style.width = `${percent}%`;
                        }
                    });
                    promptAudio._hasProgressListener = true;
                }
                
                // Set up status updates if not already set
                if (!promptAudio._hasStatusListeners) {
                    promptAudio.addEventListener('playing', () => {
                        if (statusElement) statusElement.textContent = 'Playing reference audio...';
                    });
                    
                    promptAudio.addEventListener('ended', () => {
                        if (statusElement) statusElement.textContent = 'Reference audio complete';
                    });
                    promptAudio._hasStatusListeners = true;
                }
                
                // Play the audio
                promptAudio.play()
                    .then(() => console.log('Prompt audio playback started'))
                    .catch(e => {
                        console.error('Auto-play prevented:', e);
                        if (statusElement) statusElement.textContent = 'Click anywhere to play audio';
                        
                        // Add click handler to play audio
                        document.addEventListener('click', function playOnClick() {
                            promptAudio.play()
                                .then(() => {
                                    document.removeEventListener('click', playOnClick);
                                })
                                .catch(console.error);
                        }, { once: true });
                    });
            }
        } else if (currentPage < totalPages - 1) {
            // Model page
            const modelIndex = currentPage - 1;
            console.log(`Model index: ${modelIndex}, MODELS: ${JSON.stringify(MODELS)}`);
            
            if (modelIndex < 0 || modelIndex >= MODELS.length) {
                console.error(`Invalid model index: ${modelIndex}, MODELS length: ${MODELS.length}`);
                return;
            }
            
            const model = MODELS[modelIndex];
            console.log(`Selected model: ${model}`);
            const modelAudio = audioElements[model];
            const progressElement = document.getElementById(`${model}-progress`);
            const statusElement = document.getElementById(`${model}-status`);
            
            if (!modelAudio) {
                console.error(`Audio element for model ${model} not found!`);
                console.log('Available audio elements:', Object.keys(audioElements));
                return;
            }
            
            console.log(`Playing ${model} audio automatically`);
            
            // Set up progress tracking if not already set
            if (!modelAudio._hasProgressListener) {
                modelAudio.addEventListener('timeupdate', () => {
                    if (modelAudio.duration) {
                        const percent = (modelAudio.currentTime / modelAudio.duration) * 100;
                        if (progressElement) progressElement.style.width = `${percent}%`;
                    }
                });
                modelAudio._hasProgressListener = true;
            }
            
            // Set up status updates if not already set
            if (!modelAudio._hasStatusListeners) {
                modelAudio.addEventListener('playing', () => {
                    if (statusElement) statusElement.textContent = `Playing sample ${modelIndex + 1}...`;
                });
                
                modelAudio.addEventListener('ended', () => {
                    if (statusElement) statusElement.textContent = `Sample ${modelIndex + 1} complete`;
                });
                modelAudio._hasStatusListeners = true;
            }
            
            // Play the audio
            modelAudio.play()
                .then(() => console.log(`${model} audio playback started`))
                .catch(e => {
                    console.error('Auto-play prevented:', e);
                    if (statusElement) statusElement.textContent = 'Click anywhere to play audio';
                    
                    // Add click handler to play audio
                    document.addEventListener('click', function playOnClick() {
                        modelAudio.play()
                            .then(() => {
                                document.removeEventListener('click', playOnClick);
                            })
                            .catch(console.error);
                    }, { once: true });
                });
        }
    }
    
    // Function to update ratings summary
    function updateRatingsSummary() {
        const summaryContainer = document.getElementById('ratings-summary');
        if (!summaryContainer) return;
        
        // Clear existing content
        summaryContainer.innerHTML = '';
        
        // Create summary for each model
        MODELS.forEach(model => {
            if (!answers[model]) return;
            
            const modelSummary = document.createElement('div');
            modelSummary.className = 'model-summary';
            
            const modelTitle = document.createElement('h3');
            modelTitle.textContent = `Sample ${MODELS.indexOf(model) + 1}`;
            modelSummary.appendChild(modelTitle);
            
            // Add each metric rating
            Object.entries(answers[model] || {}).forEach(([metric, value]) => {
                const metricSummary = document.createElement('div');
                metricSummary.className = 'metric-summary';
                
                const metricName = document.createElement('div');
                metricName.className = 'metric-name';
                metricName.textContent = metric;
                
                const metricValue = document.createElement('div');
                metricValue.className = 'metric-value';
                metricValue.textContent = value;
                
                metricSummary.appendChild(metricName);
                metricSummary.appendChild(metricValue);
                modelSummary.appendChild(metricSummary);
            });
            
            summaryContainer.appendChild(modelSummary);
        });
    }
    
    // Check if all metrics for a specific model are rated
    function checkModelMetricsRated(model) {
        if (!answers[model]) return false;
        
        const allRated = METRICS.every(metric => answers[model][metric] !== undefined);
        
        // If all metrics for this model are rated, enable navigation to next page
        if (allRated) {
            // Enable swiping to next page
            navRight.style.pointerEvents = 'auto';
            
            // Auto-advance after a short delay
            setTimeout(() => {
                if (currentPage < totalPages - 1) {
                    goToPage(currentPage + 1);
                }
            }, 1000);
        }
        
        return allRated;
    }
    
    // Check if all metrics have been rated for all models
    function checkAllMetricsRated() {
        const allModelsRated = MODELS.every(model => {
            if (!answers[model]) return false;
            return METRICS.every(metric => answers[model][metric] !== undefined);
        });
        
        nextButton.disabled = !allModelsRated;
        return allModelsRated;
    }
    
    // Handle navigation buttons
    prevButton.addEventListener('click', function() {
        goToPage(currentPage - 1);
    });
    
    nextButton.addEventListener('click', async function() {
        // Show loading indicator
        loadingIndicator.style.display = 'block';
        
        try {
            // Calculate time spent
            const timeSpent = (Date.now() - startTime) / 1000;
            
            // Flatten answers for API compatibility
            const flattenedAnswers = {};
            
            // For each model, add its metrics to the flattened answers
            Object.entries(answers).forEach(([model, modelAnswers]) => {
                Object.entries(modelAnswers).forEach(([metric, value]) => {
                    // Create a composite key that includes the model and metric
                    const compositeKey = `${model}_${metric}`;
                    flattenedAnswers[compositeKey] = value;
                });
            });
            
            // Save answers
            const response = await fetch('/api/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    questionId: QUESTION_ID,
                    answers: flattenedAnswers,
                    timeSpent: timeSpent
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Navigate to next question or finish
                window.location.href = NEXT_URL;
            } else {
                alert('Error saving answers: ' + (result.error || 'Unknown error'));
                loadingIndicator.style.display = 'none';
            }
        } catch (error) {
            console.error('Error saving answers:', error);
            alert('Error saving answers. Please try again.');
            loadingIndicator.style.display = 'none';
        }
    });
    
    // Handle rating button clicks
    document.querySelectorAll('.rating-button').forEach(button => {
        button.addEventListener('click', function() {
            const metricElement = button.closest('.metric');
            const metric = metricElement.dataset.metric;
            const model = metricElement.dataset.model;
            const value = parseInt(button.dataset.value);
            
            // Update selected state
            metricElement.querySelectorAll('.rating-button').forEach(btn => {
                btn.classList.toggle('selected', btn === button);
            });
            
            // Store answer - organize by model
            if (!answers[model]) {
                answers[model] = {};
            }
            answers[model][metric] = value;
            
            // Check if all metrics for this model are rated
            checkModelMetricsRated(model);
        });
    });
    
    // Handle navigation clicks
    navLeft.addEventListener('click', function() {
        console.log('Left navigation clicked, going to previous page');
        if (currentPage > 0) {
            goToPage(currentPage - 1);
        }
    });
    
    navRight.addEventListener('click', function() {
        console.log('Right navigation clicked, going to next page');
        if (currentPage < totalPages - 1) {
            goToPage(currentPage + 1);
        }
    });
    
    // Handle keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowLeft') {
            console.log('Left arrow key pressed, going to previous page');
            if (currentPage > 0) {
                goToPage(currentPage - 1);
            }
        } else if (e.key === 'ArrowRight') {
            console.log('Right arrow key pressed, going to next page');
            if (currentPage < totalPages - 1) {
                goToPage(currentPage + 1);
            }
        }
    });
    
    // Handle touch events for swipe
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    });
    
    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });
    
    function handleSwipe() {
        const swipeThreshold = 50;
        
        if (touchEndX < touchStartX - swipeThreshold) {
            // Swipe left to right
            console.log('Swipe detected (left to right), going to next page');
            if (currentPage < totalPages - 1) {
                goToPage(currentPage + 1);
            }
        } else if (touchEndX > touchStartX + swipeThreshold) {
            // Swipe right to left
            console.log('Swipe detected (right to left), going to previous page');
            if (currentPage > 0) {
                goToPage(currentPage - 1);
            }
        }
    }
    
    // Send heartbeat to keep session alive
    setInterval(async function() {
        try {
            await fetch('/api/heartbeat');
        } catch (error) {
            console.error('Heartbeat error:', error);
        }
    }, 60000); // Every minute
    
    // Initialize
    initAudio();
    
    // Play audio for the initial page
    setTimeout(function() {
        console.log('Initial page load, playing audio automatically');
        playAudioForCurrentPage();
    }, 500);
});