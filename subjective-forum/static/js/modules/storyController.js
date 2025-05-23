/**
 * Story Controller Module
 * 
 * Handles the Instagram-like story navigation and interaction.
 */
import audioLoader from './audioLoader.js';
import * as api from './api.js';

/**
 * StoryController class for managing story-like navigation
 */
export class StoryController {
    /**
     * Create a new StoryController instance
     * @param {Object} options - Configuration options
     * @param {string} options.storySelector - CSS selector for the story container
     * @param {string} options.pageSelector - CSS selector for story pages
     * @param {string} options.progressSelector - CSS selector for progress segments
     * @param {string} options.leftNavSelector - CSS selector for left navigation area
     * @param {string} options.rightNavSelector - CSS selector for right navigation area
     * @param {Function} options.onPageChange - Callback when page changes
     * @param {Function} options.onComplete - Callback when story is completed
     */
    constructor(options) {
        this.options = Object.assign({
            storySelector: '.story',
            pageSelector: '.story-page',
            progressSelector: '.progress-segment',
            leftNavSelector: '.story-nav-left',
            rightNavSelector: '.story-nav-right',
            onPageChange: null,
            onComplete: null
        }, options);
        
        // Elements
        this.storyElement = document.querySelector(this.options.storySelector);
        this.pages = Array.from(document.querySelectorAll(this.options.pageSelector));
        this.progressSegments = Array.from(document.querySelectorAll(this.options.progressSelector));
        this.leftNav = document.querySelector(this.options.leftNavSelector);
        this.rightNav = document.querySelector(this.options.rightNavSelector);
        
        // State
        this.currentPage = 0;
        this.totalPages = this.pages.length;
        this.startTime = Date.now();
        this.audioElements = new Map();
        this.touchStartX = 0;
        this.touchEndX = 0;
        
        // Initialize
        this.init();
    }
    
    /**
     * Initialize the story controller
     */
    init() {
        // Set up navigation event listeners
        this.setupNavigation();
        
        // Set up touch events for swipe
        this.setupTouchEvents();
        
        // Set up keyboard navigation
        this.setupKeyboardNavigation();
        
        // Initialize audio elements
        this.initAudio();
        
        // Go to the first page
        this.goToPage(0);
    }
    
    /**
     * Set up navigation event listeners
     */
    setupNavigation() {
        // Left navigation (previous)
        if (this.leftNav) {
            this.leftNav.addEventListener('click', () => {
                if (this.currentPage > 0) {
                    this.goToPage(this.currentPage - 1);
                }
            });
        }
        
        // Right navigation (next)
        if (this.rightNav) {
            this.rightNav.addEventListener('click', () => {
                if (this.currentPage < this.totalPages - 1) {
                    this.goToPage(this.currentPage + 1);
                }
            });
        }
    }
    
    /**
     * Set up touch events for swipe navigation
     */
    setupTouchEvents() {
        document.addEventListener('touchstart', (e) => {
            this.touchStartX = e.changedTouches[0].screenX;
        });
        
        document.addEventListener('touchend', (e) => {
            this.touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe();
        });
    }
    
    /**
     * Handle swipe gestures
     */
    handleSwipe() {
        const swipeThreshold = 50;
        
        if (this.touchEndX < this.touchStartX - swipeThreshold) {
            // Swipe left to right (next)
            if (this.currentPage < this.totalPages - 1) {
                this.goToPage(this.currentPage + 1);
            }
        } else if (this.touchEndX > this.touchStartX + swipeThreshold) {
            // Swipe right to left (previous)
            if (this.currentPage > 0) {
                this.goToPage(this.currentPage - 1);
            }
        }
    }
    
    /**
     * Set up keyboard navigation
     */
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                if (this.currentPage > 0) {
                    this.goToPage(this.currentPage - 1);
                }
            } else if (e.key === 'ArrowRight') {
                if (this.currentPage < this.totalPages - 1) {
                    this.goToPage(this.currentPage + 1);
                }
            }
        });
    }
    
    /**
     * Initialize audio elements
     */
    initAudio() {
        // Find all audio elements in the story
        const audioElements = this.storyElement.querySelectorAll('audio[data-src]');
        
        // Initialize each audio element
        audioElements.forEach(audio => {
            const src = audio.dataset.src;
            const id = audio.id;
            
            // Set the source
            audio.src = src;
            
            // Store the audio element
            this.audioElements.set(id, audio);
            
            // Preload the audio
            audio.load();
        });
    }
    
    /**
     * Navigate to a specific page
     * @param {number} pageIndex - Index of the page to navigate to
     */
    goToPage(pageIndex) {
        if (pageIndex < 0 || pageIndex >= this.totalPages) return;
        
        // Update current page
        this.currentPage = pageIndex;
        
        // Scroll to the page
        if (this.pages[pageIndex]) {
            this.pages[pageIndex].scrollIntoView({ behavior: 'smooth' });
        }
        
        // Update progress bar
        this.updateProgress();
        
        // Auto-play audio if present on this page
        this.playPageAudio(pageIndex);
        
        // Call the onPageChange callback if provided
        if (typeof this.options.onPageChange === 'function') {
            this.options.onPageChange(pageIndex, this.totalPages);
        }
        
        // Check if we've reached the end
        if (pageIndex === this.totalPages - 1) {
            this.onLastPage();
        }
    }
    
    /**
     * Update the progress bar
     */
    updateProgress() {
        this.progressSegments.forEach((segment, i) => {
            segment.classList.toggle('active', i <= this.currentPage);
        });
    }
    
    /**
     * Play audio on the current page if available
     * @param {number} pageIndex - Index of the current page
     */
    playPageAudio(pageIndex) {
        // Find audio element on the current page
        const currentPage = this.pages[pageIndex];
        if (!currentPage) return;
        
        const audioElement = currentPage.querySelector('audio');
        if (audioElement) {
            // Try to play the audio (may be blocked by autoplay policy)
            setTimeout(() => {
                audioElement.play().catch(e => {
                    console.log('Auto-play prevented:', e);
                });
            }, 500);
        }
    }
    
    /**
     * Actions to take when reaching the last page
     */
    onLastPage() {
        if (typeof this.options.onComplete === 'function') {
            this.options.onComplete();
        }
    }
    
    /**
     * Get the time spent in the story
     * @returns {number} - Time spent in seconds
     */
    getTimeSpent() {
        return (Date.now() - this.startTime) / 1000;
    }
    
    /**
     * Reset the timer
     */
    resetTimer() {
        this.startTime = Date.now();
    }
    
    /**
     * Pause all audio elements
     */
    pauseAllAudio() {
        this.audioElements.forEach(audio => {
            audio.pause();
        });
    }
    
    /**
     * Clean up resources
     */
    destroy() {
        // Pause all audio
        this.pauseAllAudio();
        
        // Remove event listeners (simplified - in a real implementation you would
        // need to remove the specific event listeners that were added)
    }
}

/**
 * Create a story controller for the question interface
 * @param {Object} options - Configuration options
 * @returns {StoryController} - The story controller instance
 */
export function createQuestionStory(options) {
    return new StoryController(options);
}