/**
 * INNOVATE AI - Video Synchronization Module
 * Handles synchronization between audio output and video avatar animation
 */

class VideoSync {
    constructor(videoElement) {
        this.video = videoElement;
        this.isPlaying = false;
        this.isLoaded = false;
        
        // Make sure to have a video source
        if (!this.video.src && !this.video.querySelector('source')) {
            this.setSource('/static/assets/innovate.mp4');
        }
        
        this.bindEvents();
    }
    
    /**
     * Bind video event listeners
     */
    bindEvents() {
        this.video.addEventListener('loadeddata', () => {
            this.isLoaded = true;
            console.log('Video loaded successfully');
        });
        
        this.video.addEventListener('error', (e) => {
            console.error('Error loading video:', e);
        });
        
        this.video.addEventListener('ended', () => {
            this.reset();
        });
    }
    
    /**
     * Start playing the video in sync with audio
     * @returns {boolean} Success indicator
     */
    play() {
        if (!this.isLoaded) {
            console.warn('Video not loaded yet');
            return false;
        }
        
        // Reset to beginning if at end
        if (this.video.ended || this.video.currentTime >= this.video.duration - 0.1) {
            this.video.currentTime = 0;
        }
        
        try {
            // Start playback
            const playPromise = this.video.play();
            
            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        this.isPlaying = true;
                        this.updateVideoActiveState(true);
                    })
                    .catch(error => {
                        console.error('Error playing video:', error);
                        // Auto-play was prevented, try muting and playing
                        this.video.muted = true;
                        this.video.play().catch(e => {
                            console.error('Failed to play video even when muted:', e);
                        });
                    });
            }
            
            return true;
        } catch (error) {
            console.error('Error in play():', error);
            return false;
        }
    }
    
    /**
     * Pause the video
     */
    pause() {
        if (this.isPlaying) {
            this.video.pause();
            this.isPlaying = false;
            this.updateVideoActiveState(false);
        }
    }
    
    /**
     * Reset the video to the beginning and pause
     */
    reset() {
        this.video.currentTime = 0;
        this.pause();
    }
    
    /**
     * Update the active state of the video for visual feedback
     * @param {boolean} isActive Whether video is active
     */
    updateVideoActiveState(isActive) {
        if (isActive) {
            this.video.classList.add('avatar-active');
        } else {
            this.video.classList.remove('avatar-active');
        }
    }
    
    /**
     * Get the current state of the video
     * @returns {Object} Video state
     */
    getState() {
        return {
            isPlaying: this.isPlaying,
            isLoaded: this.isLoaded,
            currentTime: this.video.currentTime,
            duration: this.video.duration
        };
    }
    
    /**
     * Initialize the video with a specific source
     * @param {string} videoSrc URL of the video source
     */
    setSource(videoSrc) {
        this.isLoaded = false;
        this.video.src = videoSrc;
        this.video.load();
    }
}