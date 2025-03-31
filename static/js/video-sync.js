/**
 * INNOVATE AI - Video Synchronization Module
 * Handles synchronization between audio output and video avatar animation
 */

class VideoSync {
    constructor(videoElement) {
        this.video = videoElement;
        this.playing = false;
        
        if (this.video) {
            this.bindEvents();
        } else {
            console.error('Video element not found');
        }
    }

    /**
     * Bind video event listeners
     */
    bindEvents() {
        // When video is loaded, make sure it's paused at the start
        this.video.addEventListener('loadedmetadata', () => {
            this.reset();
        });
        
        // Handle video errors
        this.video.addEventListener('error', (e) => {
            console.error('Video error:', e);
        });
        
        // Handle video end
        this.video.addEventListener('ended', () => {
            this.updateVideoActiveState(false);
            this.reset();
        });
    }

    /**
     * Start playing the video in sync with audio
     * @returns {boolean} Success indicator
     */
    play() {
        if (!this.video) return false;
        
        try {
            // Reset video to start if it was at the end
            if (this.video.ended || this.video.currentTime >= this.video.duration - 0.1) {
                this.video.currentTime = 0;
            }
            
            // Play the video
            const playPromise = this.video.play();
            
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    this.playing = true;
                    this.updateVideoActiveState(true);
                }).catch(error => {
                    console.error('Video play error:', error);
                    this.playing = false;
                });
            }
            
            return true;
        } catch (error) {
            console.error('Error playing video:', error);
            return false;
        }
    }

    /**
     * Pause the video
     */
    pause() {
        if (!this.video) return;
        
        try {
            this.video.pause();
            this.playing = false;
            this.updateVideoActiveState(false);
        } catch (error) {
            console.error('Error pausing video:', error);
        }
    }

    /**
     * Reset the video to the beginning and pause
     */
    reset() {
        if (!this.video) return;
        
        try {
            this.video.currentTime = 0;
            this.video.pause();
            this.playing = false;
            this.updateVideoActiveState(false);
        } catch (error) {
            console.error('Error resetting video:', error);
        }
    }

    /**
     * Update the active state of the video for visual feedback
     * @param {boolean} isActive Whether video is active
     */
    updateVideoActiveState(isActive) {
        if (!this.video) return;
        
        if (isActive) {
            this.video.classList.add('active');
            
            // Get the video container and update its state if it exists
            const videoWrapper = this.video.closest('.video-wrapper');
            if (videoWrapper) {
                videoWrapper.classList.add('active');
            }
            
            // Update status indicator if it exists
            const statusDot = document.querySelector('.status-dot');
            if (statusDot) {
                statusDot.classList.add('active');
            }
        } else {
            this.video.classList.remove('active');
            
            // Get the video container and update its state if it exists
            const videoWrapper = this.video.closest('.video-wrapper');
            if (videoWrapper) {
                videoWrapper.classList.remove('active');
            }
            
            // Update status indicator if it exists
            const statusDot = document.querySelector('.status-dot');
            if (statusDot) {
                statusDot.classList.remove('active');
            }
        }
    }

    /**
     * Get the current state of the video
     * @returns {Object} Video state
     */
    getState() {
        if (!this.video) return { playing: false, duration: 0, currentTime: 0 };
        
        return {
            playing: this.playing,
            duration: this.video.duration || 0,
            currentTime: this.video.currentTime || 0,
            volume: this.video.volume,
            muted: this.video.muted,
            error: this.video.error
        };
    }

    /**
     * Initialize the video with a specific source
     * @param {string} videoSrc URL of the video source
     */
    setSource(videoSrc) {
        if (!this.video) return;
        
        this.video.src = videoSrc;
        this.video.load();
    }
}