/**
 * INNOVATE AI - Audio Processing Module
 * Handles audio recording, processing, and playback
 */

class AudioProcessor {
    constructor() {
        this.audioContext = null;
        this.microphone = null;
        this.recorder = null;
        this.analyser = null;
        this.currentRecording = null;
        this.isRecording = false;
        this.audioData = [];
        this.frequencyData = null;
    }

    /**
     * Initialize audio context
     * @returns {Promise<boolean>} Success indicator
     */
    async initialize() {
        try {
            // Create audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
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
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
            
            // Create source from microphone
            this.microphone = this.audioContext.createMediaStreamSource(stream);
            
            // Set up analyser for visualization
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.frequencyData = new Uint8Array(this.analyser.frequencyBinCount);
            
            // Connect microphone to analyser
            this.microphone.connect(this.analyser);
            
            return stream;
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
            if (!this.microphone) {
                await this.requestMicrophoneAccess();
            }

            this.audioData = [];
            this.isRecording = true;
            
            // Set up MediaRecorder
            const stream = this.microphone.mediaStream;
            this.recorder = new MediaRecorder(stream);
            
            // Set up recorder event handlers
            this.recorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioData.push(event.data);
                    if (onDataAvailable) {
                        onDataAvailable(event.data);
                    }
                }
            };
            
            this.recorder.onstop = () => {
                this.isRecording = false;
                const blob = new Blob(this.audioData, { type: 'audio/wav' });
                if (onComplete) {
                    onComplete(blob);
                }
            };
            
            // Start recording
            this.recorder.start(100); // Collect data every 100ms
        } catch (error) {
            console.error('Error starting recording:', error);
            this.isRecording = false;
            throw error;
        }
    }

    /**
     * Stop recording audio
     */
    stopRecording() {
        if (this.recorder && this.isRecording) {
            this.recorder.stop();
            this.isRecording = false;
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
        if (this.analyser && this.frequencyData) {
            this.analyser.getByteFrequencyData(this.frequencyData);
            return this.frequencyData;
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
        const audio = new Audio(audioUrl);
        
        // Set event listeners
        audio.addEventListener('play', () => {
            if (onPlay) onPlay();
        });
        
        audio.addEventListener('ended', () => {
            if (onEnd) onEnd();
        });
        
        // Play the audio
        audio.play()
            .catch(error => console.error('Error playing audio:', error));
        
        return audio;
    }

    /**
     * Clean up resources
     */
    cleanup() {
        // Stop recording if active
        if (this.isRecording) {
            this.stopRecording();
        }
        
        // Disconnect microphone
        if (this.microphone) {
            this.microphone.disconnect();
            this.microphone = null;
        }
        
        // Close audio context
        if (this.audioContext) {
            this.audioContext.close()
                .catch(error => console.error('Error closing audio context:', error));
        }
    }
}