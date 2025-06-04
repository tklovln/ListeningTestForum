// Story controller
document.addEventListener('DOMContentLoaded', function() {
    const mainProgressBarFill = document.getElementById('progress-bar-fill');

    // Get data from HTML attributes
    const storyContainer = document.querySelector('.story-container');
    const QUESTION_ID = storyContainer.getAttribute('data-question-id');
    const PROMPT_ID = storyContainer.getAttribute('data-prompt-id');
    const AUDIO_SUBFOLDER = storyContainer.getAttribute('data-audio-subfolder');
    
    // Initialization
    let MODELS = [];
    let METRICS = [];

    // Populate MODELS and METRICS from the embedded JSON script tag
    const jsonDataElement = document.getElementById('question-data-json');
    if (jsonDataElement) {
        try {
            const jsonData = JSON.parse(jsonDataElement.textContent);
            
            // Populate MODELS
            if (jsonData.models && Array.isArray(jsonData.models) && jsonData.models.length > 0) {
                MODELS = jsonData.models;
                console.log('Successfully parsed MODELS from JSON script:', JSON.stringify(MODELS));
            } else {
                console.warn('MODELS from JSON script is not a non-empty array or not found. MODELS will be empty.');
            }

            // Populate METRICS
            if (jsonData.metrics && Array.isArray(jsonData.metrics)) {
                // Validate if it's an array of objects with 'name'
                if (jsonData.metrics.length > 0 &&
                    (typeof jsonData.metrics[0] !== 'object' || jsonData.metrics[0] === null || !('name' in jsonData.metrics[0]))) {
                    console.error('Parsed METRICS from JSON script does not seem to be an array of metric objects. METRICS will be empty.', JSON.stringify(jsonData.metrics));
                } else {
                    METRICS = jsonData.metrics;
                    console.log('Successfully parsed METRICS (array of objects) from JSON script:', JSON.stringify(METRICS));
                }
            } else {
                console.warn('METRICS from JSON script is not an array or not found. METRICS will be empty.');
            }

        } catch (error) {
            console.error('Failed to parse JSON from script tag for MODELS/METRICS. Both will be empty.', error);
        }
    } else {
        console.warn('JSON data script tag (#question-data-json) not found. MODELS and METRICS will be empty.');
    }
    
    // Fallback for MODELS and METRICS if still empty
    if (MODELS.length === 0) {
        console.error("CRITICAL: MODELS array is empty after all parsing attempts. Using hardcoded emergency fallback.");
        MODELS = ["gt", "methodA", "methodB"]; // Emergency fallback
    }
    if (METRICS.length === 0) {
        console.error("CRITICAL: METRICS array is empty after all parsing attempts. Using hardcoded emergency fallback.");
        // This fallback needs to be an array of objects
        METRICS = [
            {name: "連貫性（Consistency）", description: "Default description"},
            {name: "豐富性（Richness）", description: "Default description"},
            {name: "一致性（Coherence）", description: "Default description"}, // Corrected from Consistency
            {name: "整體評價（Overall Rating）", description: "Default description"}
        ];
    }
    
    console.log('Final MODELS:', JSON.stringify(MODELS));
    console.log('Final METRICS:', JSON.stringify(METRICS)); // Should be array of objects
    
    const IS_LAST = storyContainer.getAttribute('data-is-last') === 'true';
    const NEXT_URL = storyContainer.getAttribute('data-next-url');
    const PREV_URL = storyContainer.getAttribute('data-prev-url');
    const AUDIO_ROOT = storyContainer.getAttribute('data-audio-root');
    const DEBUG_MODE = storyContainer.getAttribute('data-debug-mode') === 'true';
    
    // Elements
    const storyElement = document.getElementById('story');
    const progressSegments = document.getElementById('progress-segments');
    const navLeft = document.getElementById('nav-left');
    const navRight = document.getElementById('nav-right');
    const loadingIndicator = document.getElementById('loading-indicator');
    // const prevButton = document.getElementById('prev-button'); // Obsolete
    // const nextButton = document.getElementById('next-button'); // Obsolete
    
    // State
    let currentPage = 0;
    // Calculate total pages: 1 prompt page + model pages (no summary page)
    const totalPages = 1 + MODELS.length;
    console.log(`Total pages: ${totalPages} (1 prompt page + ${MODELS.length} model pages)`);
    let startTime = Date.now();
    let answers = {};
    let audioElements = {};
    let audioLoaded = {};

    // For main top progress bar animation
    let mainProgressBarAnimationId = null;
    let mainProgressBarStartWidth = 0; // Percentage width where current question's segment starts
    let mainProgressBarTargetWidth = 0; // Percentage width where current question's segment ends

    if (mainProgressBarFill && typeof window.CURRENT_QUESTION_INDEX === 'number' && typeof window.TOTAL_QUESTIONS === 'number' && window.TOTAL_QUESTIONS > 0) {
        const initialMainSegmentStartPct = (window.CURRENT_QUESTION_INDEX / window.TOTAL_QUESTIONS) * 100;
        mainProgressBarFill.style.width = initialMainSegmentStartPct + '%';
        console.log(`Main progress bar initialised to start of segment: ${initialMainSegmentStartPct.toFixed(2)}% for Q${window.CURRENT_QUESTION_INDEX + 1}`);
    }
    
    // Initialize progress bar for story pages (within a question)
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
                const promptAudioFilename = AUDIO_SUBFOLDER ? `${AUDIO_SUBFOLDER}/${PROMPT_ID}_prompt.mp3` : `${PROMPT_ID}_prompt.mp3`;
                const promptUrl = `${window.location.origin}/api/audio/${promptAudioFilename}`;
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
                    const modelAudioFilename = AUDIO_SUBFOLDER ? `${AUDIO_SUBFOLDER}/${PROMPT_ID}_${model}.mp3` : `${PROMPT_ID}_${model}.mp3`;
                    const modelUrl = `${window.location.origin}/api/audio/${modelAudioFilename}`;
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
    
    /**
     * Custom smooth scroll function.
     * @param {HTMLElement} scrollContainer - The container element that scrolls.
     * @param {HTMLElement} targetElement - The element to scroll to.
     * @param {number} duration - The duration of the scroll animation in milliseconds.
     */
    function customSmoothScrollTo(scrollContainer, targetElement, duration) {
        const targetScrollLeft = targetElement.offsetLeft;
        const startScrollLeft = scrollContainer.scrollLeft;
        const distance = targetScrollLeft - startScrollLeft;
        let startTime = null;

        function animation(currentTime) {
            if (startTime === null) startTime = currentTime;
            const timeElapsed = currentTime - startTime;
            let t = Math.min(timeElapsed / duration, 1); // progress: 0 to 1

            // Ease-out Cubic easing function: 1 - (1-t)^3
            const easedProgress = 1 - Math.pow(1 - t, 3);

            scrollContainer.scrollLeft = startScrollLeft + distance * easedProgress;

            if (timeElapsed < duration) {
                requestAnimationFrame(animation);
            } else {
                scrollContainer.scrollLeft = targetScrollLeft; // Ensure it ends exactly at the target
            }
        }
        requestAnimationFrame(animation);
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
            const replayIconElement = document.getElementById('prompt-replay-icon');
            const audioIndicatorElement = progressElement ? progressElement.closest('.audio-indicator') : null;

            if (promptAudio) {
                console.log('Playing prompt audio automatically');

                // Animate main progress bar with prompt audio
                if (mainProgressBarFill && typeof window.CURRENT_QUESTION_INDEX === 'number' && typeof window.TOTAL_QUESTIONS === 'number' && window.TOTAL_QUESTIONS > 0) {
                    if (!promptAudio._mainProgressBarAnimatorAttached) {
                        const mainSegmentStartPct = (window.CURRENT_QUESTION_INDEX / window.TOTAL_QUESTIONS) * 100;
                        const mainSegmentEndPct = ((window.CURRENT_QUESTION_INDEX + 1) / window.TOTAL_QUESTIONS) * 100;
                        
                        // Ensure bar starts at the beginning of its segment visually if not already there
                        // This might happen if audio auto-play is delayed or user interacts quickly
                        if (parseFloat(mainProgressBarFill.style.width) < mainSegmentStartPct) {
                             mainProgressBarFill.style.width = mainSegmentStartPct + '%';
                        }

                        const animateMainProgress = () => {
                            if (promptAudio.duration > 0) {
                                const audioProgressRatio = promptAudio.currentTime / promptAudio.duration;
                                const currentMainBarWidth = mainSegmentStartPct + (audioProgressRatio * (mainSegmentEndPct - mainSegmentStartPct));
                                mainProgressBarFill.style.width = Math.min(currentMainBarWidth, mainSegmentEndPct) + '%';
                            }
                        };

                        const onPromptAudioEndedForMainBar = () => {
                            mainProgressBarFill.style.width = mainSegmentEndPct + '%';
                            promptAudio.removeEventListener('timeupdate', animateMainProgress);
                            promptAudio.removeEventListener('ended', onPromptAudioEndedForMainBar);
                            promptAudio._mainProgressBarAnimatorAttached = false;
                            console.log(`Main progress bar animation ended for Q${window.CURRENT_QUESTION_INDEX + 1}, set to ${mainSegmentEndPct.toFixed(2)}%`);
                        };

                        promptAudio.addEventListener('timeupdate', animateMainProgress);
                        promptAudio.addEventListener('ended', onPromptAudioEndedForMainBar);
                        promptAudio._mainProgressBarAnimatorAttached = true;
                        console.log(`Main progress bar animation attached for Q${window.CURRENT_QUESTION_INDEX + 1}. Start: ${mainSegmentStartPct.toFixed(2)}%, End: ${mainSegmentEndPct.toFixed(2)}%`);
                    }
                }
                
                // Set up progress tracking for the individual prompt audio bar
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
                        if (statusElement) statusElement.style.display = 'inline';
                        if (replayIconElement) replayIconElement.style.display = 'none';
                        if (statusElement) {
                            // let statusText = 'Playing reference audio...';
                            let statusText = '';
                            if (DEBUG_MODE) {
                                const srcFilename = promptAudio.src.split('/').pop();
                                const [debugPromptId, debugModelTypeWithExt] = srcFilename.split('_');
                                const debugModelType = debugModelTypeWithExt.replace('.mp3', '');
                                statusText += ` (ID: ${debugPromptId}, Type: ${debugModelType})`;
                            }
                            statusElement.textContent = statusText;
                        }
                    });
                    
                    promptAudio.addEventListener('ended', () => {
                        if (statusElement) statusElement.style.display = 'none';
                        if (replayIconElement) replayIconElement.style.display = 'inline';
                        // No need to set text content if statusElement is hidden
                    });
                    promptAudio._hasStatusListeners = true;
                }

                if (!promptAudio._hasReplayListener) {
                    const replayHandler = () => {
                        promptAudio.currentTime = 0;
                        promptAudio.play();
                    };
                    if (audioIndicatorElement) {
                        audioIndicatorElement.addEventListener('click', replayHandler);
                    }
                    if (replayIconElement) {
                        replayIconElement.addEventListener('click', replayHandler);
                    }
                    promptAudio._hasReplayListener = true;
                }
                
                // Play the audio
                promptAudio.play()
                    .then(() => console.log('Prompt audio playback started'))
                    .catch(e => {
                        console.error('Auto-play prevented for prompt audio:', e);
                        if (statusElement) {
                            let statusText = 'Click anywhere to play reference audio';
                             if (DEBUG_MODE) {
                                const srcFilename = promptAudio.src.split('/').pop();
                                const [debugPromptId, debugModelTypeWithExt] = srcFilename.split('_');
                                const debugModelType = debugModelTypeWithExt.replace('.mp3', '');
                                statusText += ` (ID: ${debugPromptId}, Type: ${debugModelType})`;
                            }
                            statusElement.textContent = statusText;
                        }
                        
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
        } else if (currentPage < totalPages) {
            // Model page
            const modelIndex = currentPage - 1;
            console.log(`Model index: ${modelIndex}, MODELS: ${JSON.stringify(MODELS)}`);
            
            if (modelIndex < 0 || modelIndex >= MODELS.length) {
                console.error(`Invalid model index: ${modelIndex}, MODELS length: ${MODELS.length}`);
                return;
            }
            
            const model = MODELS[modelIndex];
            console.log(`Selected model: ${model}`);

            // Initialize answers for this model with null for all metrics if not already done
            if (!answers[model]) {
                answers[model] = {};
                METRICS.forEach(metricObj => {
                    answers[model][metricObj.name] = null; // Initialize with null
                });
                console.log(`Initialized answers for model ${model}:`, JSON.stringify(answers[model]));
            }

            const modelAudio = audioElements[model];
            const progressElement = document.getElementById(`${model}-progress`);
            const statusElement = document.getElementById(`${model}-status`);
            const replayIconElement = document.getElementById(`${model}-replay-icon`);
            const audioIndicatorElement = progressElement ? progressElement.closest('.audio-indicator') : null;

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
                    if (statusElement) statusElement.style.display = 'inline';
                    if (replayIconElement) replayIconElement.style.display = 'none';
                    if (statusElement) {
                        // let statusText = `Playing sample ${modelIndex + 1}...`;
                        let statusText = '';
                        if (DEBUG_MODE) {
                            const srcFilename = modelAudio.src.split('/').pop();
                            const [debugPromptId, debugModelTypeWithExt] = srcFilename.split('_');
                            const debugModelType = debugModelTypeWithExt.replace('.mp3', '');
                            statusText += ` (ID: ${debugPromptId}, Type: ${debugModelType})`;
                        }
                        statusElement.textContent = statusText;
                    }
                });

                modelAudio.addEventListener('ended', () => {
                    if (statusElement) statusElement.style.display = 'none';
                    if (replayIconElement) replayIconElement.style.display = 'inline';
                });
                modelAudio._hasStatusListeners = true;
            }

            if (!modelAudio._hasReplayListener) {
                const replayHandler = () => {
                    modelAudio.currentTime = 0;
                    modelAudio.play();
                };
                if (audioIndicatorElement) {
                    audioIndicatorElement.addEventListener('click', replayHandler);
                }
                if (replayIconElement) {
                    replayIconElement.addEventListener('click', replayHandler);
                }
                modelAudio._hasReplayListener = true;
            }
                
            // Play the audio
            modelAudio.play()
                .then(() => console.log(`${model} audio playback started`))
                .catch(e => {
                    console.error(`Auto-play prevented for model audio (Sample ${modelIndex + 1}):`, e);
                    if (statusElement) {
                        let statusText = `Click anywhere to play sample ${modelIndex + 1}`;
                        if (DEBUG_MODE) {
                            const srcFilename = modelAudio.src.split('/').pop();
                            const [debugPromptId, debugModelTypeWithExt] = srcFilename.split('_');
                            const debugModelType = debugModelTypeWithExt.replace('.mp3', '');
                            statusText += ` (ID: ${debugPromptId}, Type: ${debugModelType})`;
                        }
                        statusElement.textContent = statusText;
                    }
                    
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
            
            // No auto-advance - require explicit navigation
            // User must click/swipe/press arrow key to proceed
        }
        
        return allRated;
    }
    
    // Function to save answers and go to next question
    async function saveAndGoToNextQuestion() {
        // Show loading indicator
        loadingIndicator.style.display = 'block';
        // document.getElementById('saving-message').style.display = 'block'; // Removed
        
        try {
            // Calculate time spent
            const timeSpent = (Date.now() - startTime) / 1000;
            
            // The 'answers' object is already in the desired nested structure:
            // answers = { model1: { metricA: value, metricB: value }, model2: { ... } }
            // No flattening needed. We will send this 'answers' object directly.
            
            const payload = {
                originalQuestionId: QUESTION_ID, // This is the template ID like "q1"
                questionIndex: window.CURRENT_QUESTION_INDEX,   // Use the global variable
                answers: answers, // Send the nested 'answers' object directly
                timeSpent: timeSpent
            };

            // Log the value just before sending
            console.log('Attempting to save answer. window.CURRENT_QUESTION_INDEX:', window.CURRENT_QUESTION_INDEX, 'Payload:', payload);
            
            // Save answers
            const response = await fetch('/api/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            const result = await response.json();
            
            if (result.success) {
                if (IS_LAST) {
                    // This is the last question, call /api/finish before redirecting to thank you page
                    try {
                        const finishResponse = await fetch('/api/finish', { method: 'POST' });
                        const finishResult = await finishResponse.json();
                        if (finishResult.success) {
                            console.log('Survey finished, final data saved. Redirecting to thank you page.');
                            window.location.href = NEXT_URL; // NEXT_URL is now thank_you.show
                        } else {
                            alert('Error finalizing survey: ' + (finishResult.error || 'Unknown error'));
                            loadingIndicator.style.display = 'none';
                        }
                    } catch (finishError) {
                        console.error('Error calling /api/finish:', finishError);
                        alert('Error finalizing survey. Please try again.');
                        loadingIndicator.style.display = 'none';
                    }
                } else {
                    // Not the last question, navigate to the next question
                    window.location.href = NEXT_URL;
                }
            } else {
                alert('Error saving answers: ' + (result.error || 'Unknown error'));
                loadingIndicator.style.display = 'none';
            }
        } catch (error) {
            console.error('Error saving answers:', error);
            alert('Error saving answers. Please try again.');
            loadingIndicator.style.display = 'none';
        }
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
    
    // Handle navigation buttons (Obsolete - these buttons were removed from HTML)
    /*
    if (prevButton) { // Check if element exists before adding listener
        prevButton.addEventListener('click', function() {
            goToPage(currentPage - 1);
        });
    }
    
    if (nextButton) { // Check if element exists before adding listener
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
    }
    */
    
    // Handle rating button clicks
    document.querySelectorAll('.rating-button').forEach(button => {
        button.addEventListener('click', function() {
            const metricElement = button.closest('.metric');
            const metric = metricElement.dataset.metricName; // Changed from dataset.metric
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
    
        function canProceedFromCurrentPage() {
            if (DEBUG_MODE) return true; // Always allow in debug mode
    
            // Check only if on a model page (currentPage > 0 means it's not the prompt page)
            // currentPage < totalPages means it's not past the last model page (which doesn't exist as a separate page)
            if (currentPage > 0 && currentPage < totalPages) {
                const modelIndex = currentPage - 1; // 0-indexed model
                const modelName = MODELS[modelIndex];
    
                console.log(`[Validation] Checking model: ${modelName}, currentPage: ${currentPage}`);
                console.log('[Validation] Current answers for this model:', JSON.stringify(answers[modelName]));
                console.log('[Validation] Expected METRICS:', JSON.stringify(METRICS.map(m => m.name)));
    
    
                if (!answers[modelName]) {
                    console.warn('[Validation] No answer object for model:', modelName);
                    alert('Please rate all metrics for the current sample before proceeding.');
                    return false;
                }
    
                const missingMetricNames = METRICS
                    .filter(metricObj => {
                        const ratedValue = answers[modelName][metricObj.name];
                        // console.log(`[Validation] Checking metric: ${metricObj.name}, Value: ${ratedValue}`);
                        return ratedValue === null; // Changed from undefined to null
                    })
                    .map(metricObj => metricObj.name);
            
            console.log('[Validation] Calculated missingMetricNames (expecting nulls for unrated):', JSON.stringify(missingMetricNames));

            if (missingMetricNames.length > 0) {
                    console.warn('[Validation] Missing ratings for metrics:', missingMetricNames.join(', '));
                    alert(`Please rate the following metrics for the current sample: ${missingMetricNames.join(', ')}`);
                    return false;
                }
                console.log('[Validation] All metrics rated for model:', modelName);
            }
            return true; // Allow proceeding from prompt page or if all checks pass on a model page
        }
    
        // --- Navigation Event Listeners ---
        const isMobile = window.innerWidth < 768; // Define mobile breakpoint

    if (!isMobile) {
        // Handle navigation clicks for non-mobile (tap areas)
        navLeft.addEventListener('click', function() {
        console.log('Left navigation clicked, going to previous page');
        if (currentPage > 0) {
            goToPage(currentPage - 1);
        }
    });
    
    navRight.addEventListener('click', function() {
        console.log('Right navigation clicked.');
        
        if (!canProceedFromCurrentPage()) {
            return; // Validation failed, stop here
        }

        // If validation passed or not applicable (e.g., on prompt page)
        if (currentPage === totalPages - 1) { // On the last model page
            console.log('Last model page: attempting to save and go to next question/finish.');
            saveAndGoToNextQuestion();
        } else if (currentPage < totalPages - 1) { // On a model page (but not the last) or on the prompt page
            console.log('Going to next sub-page (model or first model).');
            goToPage(currentPage + 1);
        } else {
            // This case should ideally not be reached if totalPages is correct (1 prompt + N models)
            // If currentPage is already at totalPages -1, the above handles it.
            // If currentPage is somehow >= totalPages, it's an issue.
            console.warn(`navRight click: currentPage (${currentPage}) is not less than totalPages-1 (${totalPages-1}), but not equal either. This might be an issue.`);
        }
    }); // This closes navRight.addEventListener
    } else { // This is the else for if (!isMobile)
        // On mobile, side tap navigation is disabled by not attaching the listeners.
        // Visual hiding can be done via CSS if preferred, but functionality is removed here.
        console.log("Mobile device detected, side tap navigation (click listeners) disabled and areas hidden. Use swipe or keyboard.");
        // If you want to also visually hide or make them non-interactive via style:
        if (navLeft) navLeft.style.display = 'none';
        if (navRight) navRight.style.display = 'none';
    }
    
    // Handle keyboard navigation (always active)
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowLeft') {
            console.log('Left arrow key pressed, going to previous page');
            if (currentPage > 0) {
                goToPage(currentPage - 1);
            }
        } else if (e.key === 'ArrowRight') {
            console.log('Right arrow key pressed.');

            if (!canProceedFromCurrentPage()) {
                return; // Validation failed, stop here
            }

            // If validation passed or not applicable
            if (currentPage === totalPages - 1) { // On the last model page
                console.log('Last model page (keyboard): attempting to save and go to next question/finish.');
                saveAndGoToNextQuestion();
            } else if (currentPage < totalPages - 1) { // On a model page (but not the last) or on the prompt page
                console.log('Going to next sub-page (model or first model) via keyboard.');
                goToPage(currentPage + 1);
            } else {
                console.warn(`ArrowRight key: currentPage (${currentPage}) is not less than totalPages-1 (${totalPages-1}), but not equal either.`);
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
        
        if (touchEndX < touchStartX - swipeThreshold) { // Swipe left (advancing to next page/sample)
            console.log('Swipe detected (left to right).');

            if (!canProceedFromCurrentPage()) {
                return; // Validation failed, stop here
            }

            // If validation passed or not applicable
            if (currentPage === totalPages - 1) { // On the last model page
                console.log('Last model page (swipe): attempting to save and go to next question/finish.');
                saveAndGoToNextQuestion();
            } else if (currentPage < totalPages - 1) { // On a model page (but not the last) or on the prompt page
                console.log('Going to next sub-page (model or first model) via swipe.');
                goToPage(currentPage + 1);
            } else {
                console.warn(`Swipe right: currentPage (${currentPage}) is not less than totalPages-1 (${totalPages-1}), but not equal either.`);
            }
        } else if (touchEndX > touchStartX + swipeThreshold) { // Swipe right (going to previous page/sample)
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

    // Metric Description Popover Logic
    const popover = document.getElementById('metric-description-popover');
    const hintButtons = document.querySelectorAll('.metric-hint-button');

    if (popover) { // Ensure popover element exists
        let currentlyOpenButton = null; // Keep track of which button's popover is open

        hintButtons.forEach(button => {
            button.addEventListener('click', function(event) {
                event.stopPropagation(); // Prevent click from bubbling up to document
                const description = this.dataset.description;

                if (popover.style.display === 'block' && currentlyOpenButton === this) {
                    // Popover is visible and for this button, so hide it
                    popover.style.display = 'none';
                    currentlyOpenButton = null;
                } else if (description) {
                    // Show or reposition popover for this button
                    popover.innerHTML = description;
                    
                    popover.style.visibility = 'hidden';
                    popover.style.display = 'block';
                    const popoverWidth = popover.offsetWidth;
                    const popoverHeight = popover.offsetHeight;
                    
                    const buttonRect = this.getBoundingClientRect();
                    
                    let top = buttonRect.bottom + window.scrollY + 8;
                    let left = buttonRect.left + window.scrollX + (buttonRect.width / 2) - (popoverWidth / 2);

                    const viewportMargin = 10;
                    if (left < viewportMargin) left = viewportMargin;
                    if (left + popoverWidth > window.innerWidth - viewportMargin) {
                        left = window.innerWidth - popoverWidth - viewportMargin;
                    }
                    if (top + popoverHeight > window.innerHeight - viewportMargin) {
                        let topAbove = buttonRect.top + window.scrollY - popoverHeight - 8;
                        if (topAbove > viewportMargin) {
                            top = topAbove;
                        } else {
                            top = window.innerHeight - popoverHeight - viewportMargin;
                        }
                    }
                    if (top < viewportMargin) top = viewportMargin;

                    const storyContainerElement = storyContainer;
                    const storyContainerRect = storyContainerElement.getBoundingClientRect();

                    popover.style.top = `${top - (storyContainerRect.top + window.scrollY)}px`;
                    popover.style.left = `${left - (storyContainerRect.left + window.scrollX)}px`;
                    
                    popover.style.visibility = 'visible';
                    currentlyOpenButton = this;
                } else {
                    // No description, ensure popover is hidden
                    popover.style.display = 'none';
                    popover.style.visibility = 'visible';
                    currentlyOpenButton = null;
                }
            });
        });

        // Hide popover if a click occurs anywhere ELSE on the document
        // (but not on the popover itself or another hint button, handled by their own listeners)
        document.addEventListener('click', function(event) {
            if (popover.style.display === 'block' && currentlyOpenButton) {
                 // Check if the click was outside the popover AND not on any hint button
                if (!popover.contains(event.target) && !event.target.classList.contains('metric-hint-button')) {
                    popover.style.display = 'none';
                    currentlyOpenButton = null;
                }
            }
        });
    } else {
        console.warn("Metric description popover element not found.");
    }
    
    // Initialize
    initAudio();
    
    // Play audio for the initial page
    setTimeout(function() {
        console.log('Initial page load, playing audio automatically');
        playAudioForCurrentPage();
    }, 500);
});
