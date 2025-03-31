/**
 * INNOVATE AI - Audio Processing Module
 * Handles audio recording, processing, and playback
 */

class AudioProcessor {
    constructor() {
        this.audioContext = null;
        this.mediaStream = null;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.analyser = null;
        this.visualizationData = null;
        
        // Audio playback
        this.currentAudio = null;
    }
    
    /**
     * Initialize audio context
     * @returns {Promise<boolean>} Success indicator
     */
    async initialize() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Set up analyser for visualization
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.visualizationData = new Uint8Array(this.analyser.frequencyBinCount);
            
            return true;
        } catch (error) {
            console.error('Error initializing audio context:', error);
            return false;
        }
    }
    
    /**
     * Request microphone access
     * @returns {Promise<MediaStream>} Media stream
     */
    async requestMicrophoneAccess() {
        try {
            this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            // Connect to analyser
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            source.connect(this.analyser);
            
            return this.mediaStream;
        } catch (error) {
            console.error('Error accessing microphone:', error);
            throw error;
        }
    }
    
    /**
     * Start recording audio
     * @param {Function} onDataAvailable Callback for when data is available
     * @param {Function} onComplete Callback for when recording is complete
     * @returns {Promise<void>}
     */
    async startRecording(onDataAvailable, onComplete) {
        if (this.isRecording) {
            return;
        }
        
        try {
            // Make sure we have microphone access
            if (!this.mediaStream) {
                await this.requestMicrophoneAccess();
            }
            
            // Reset audio chunks
            this.audioChunks = [];
            
            // Set up media recorder
            this.mediaRecorder = new MediaRecorder(this.mediaStream);
            
            // Add event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                    if (onDataAvailable) {
                        onDataAvailable(event.data);
                    }
                }
            };
            
            this.mediaRecorder.onstop = () => {
                // Create blob from chunks
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                
                // Call complete callback
                if (onComplete) {
                    onComplete(audioBlob);
                }
                
                this.isRecording = false;
            };
            
            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;
        } catch (error) {
            console.error('Error starting recording:', error);
            throw error;
        }
    }
    
    /**
     * Stop recording audio
     */
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
        }
    }
    
    /**
     * Get recording state
     * @returns {boolean} Whether recording is in progress
     */
    isCurrentlyRecording() {
        return this.isRecording;
    }
    
    /**
     * Get audio frequency data for visualization
     * @returns {Uint8Array|null} Frequency data or null if not available
     */
    getFrequencyData() {
        if (this.analyser && this.visualizationData) {
            this.analyser.getByteFrequencyData(this.visualizationData);
            return this.visualizationData;
        }
        return null;
    }
    
    /**
     * Play audio from a URL
     * @param {string} audioUrl URL of the audio to play
     * @param {Function} onPlay Callback for when audio starts playing
     * @param {Function} onEnd Callback for when audio ends
     * @returns {HTMLAudioElement} Audio element
     */
    playAudio(audioUrl, onPlay, onEnd) {
        // Stop any current playback
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
        }
        
        // Create new audio element
        this.currentAudio = new Audio(audioUrl);
        
        // Add event listeners
        if (onPlay) {
            this.currentAudio.addEventListener('play', onPlay);
        }
        
        if (onEnd) {
            this.currentAudio.addEventListener('ended', onEnd);
        }
        
        // Start playback
        this.currentAudio.play().catch(error => {
            console.error('Error playing audio:', error);
        });
        
        return this.currentAudio;
    }
    
    /**
     * Clean up resources
     */
    cleanup() {
        // Stop any ongoing recording
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
        }
        
        // Stop any ongoing playback
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }
        
        // Release microphone
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }
        
        // Close audio context
        if (this.audioContext) {
            this.audioContext.close().catch(e => console.error(e));
            this.audioContext = null;
        }
    }
}