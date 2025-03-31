/**
 * INNOVATE AI - Main Application Script
 * Handles core UI interactions, conversation management, and tool switching
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize modules
    const audioProcessor = new AudioProcessor();
    const aiTools = new AITools();
    let videoSync = null;
    
    // Initialize UI
    initializeUI();
    
    // Global variables
    let conversationHistory = [];
    let isProcessing = false;
    
    /**
     * Initialize the user interface and components
     */
    function initializeUI() {
        // Initialize audio processor
        audioProcessor.initialize()
            .then(success => {
                if (!success) {
                    addSystemMessage('Error initializing audio context. Please refresh the page and try again.');
                }
            });
        
        // Initialize tools
        aiTools.initTools();
        
        // Initialize avatar video
        initializeAvatarVideo();
        
        // Bind event listeners
        document.getElementById('mic-button').addEventListener('click', toggleRecording);
        document.getElementById('stop-button').addEventListener('click', stopRecording);
        document.getElementById('btn-clear').addEventListener('click', clearConversation);
        
        // Initialize with stop button disabled
        document.getElementById('stop-button').disabled = true;
        
        // Show initial system message
        addSystemMessage('Welcome to INNOVATE AI. Click the microphone button and speak to begin.');
    }

    /**
     * Initialize the avatar video element
     */
    function initializeAvatarVideo() {
        const videoElement = document.getElementById('avatar-video');
        
        if (videoElement) {
            videoSync = new VideoSync(videoElement);
            
            // Set video source (could be dynamic in the future)
            videoSync.setSource('/static/assets/innovate.mp4');
        } else {
            console.error('Avatar video element not found');
        }
    }

    /**
     * Toggle recording state
     */
    function toggleRecording() {
        if (audioProcessor.isCurrentlyRecording()) {
            stopRecording();
        } else {
            startRecording();
        }
    }

    /**
     * Start recording audio
     */
    function startRecording() {
        // Can't start recording if already processing
        if (isProcessing) return;
        
        // Request microphone access and start recording
        audioProcessor.startRecording(
            null, // No data available callback needed
            processAudioRecording // On complete callback
        )
        .then(() => {
            // Update UI to show recording state
            document.getElementById('mic-button').classList.add('recording');
            document.getElementById('stop-button').disabled = false;
            document.getElementById('status-text').textContent = 'Listening...';
            document.querySelector('.audio-wave').classList.add('active');
            
            // Start visualizing audio
            visualizeAudio();
        })
        .catch(error => {
            console.error('Error starting recording:', error);
            addSystemMessage('Error accessing microphone. Please make sure your microphone is connected and you have granted permission to use it.');
        });
    }

    /**
     * Stop recording audio
     */
    function stopRecording() {
        if (!audioProcessor.isCurrentlyRecording()) return;
        
        // Stop recording
        audioProcessor.stopRecording();
        
        // Update UI
        document.getElementById('mic-button').classList.remove('recording');
        document.getElementById('stop-button').disabled = true;
        document.getElementById('status-text').textContent = 'Processing...';
        document.querySelector('.audio-wave').classList.remove('active');
        
        // Stop visualization
        cancelAnimationFrame(visualizationAnimationFrame);
    }

    /**
     * Process the recorded audio
     */
    function processAudioRecording(audioBlob) {
        isProcessing = true;
        
        // Create form data for uploading
        const formData = new FormData();
        formData.append('audio', audioBlob);
        formData.append('tool_type', aiTools.getCurrentTool());
        
        // If using file search, include vector store ID if available
        if (aiTools.getCurrentTool() === 'file_search') {
            // This could be expanded to include vector store ID
            // formData.append('vector_store_id', vectorStoreId);
        }
        
        // Send audio to server for processing
        fetch('/process_speech', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add user message to conversation
                if (data.transcript) {
                    const messageId = 'msg-' + Date.now();
                    addUserMessage(data.transcript, messageId, new Date());
                    
                    // Store in history
                    conversationHistory.push({
                        role: 'user',
                        content: data.transcript,
                        timestamp: new Date(),
                        id: messageId
                    });
                }
                
                // Add AI response to conversation
                if (data.response) {
                    addAIMessage(data.response, new Date());
                    
                    // Store in history
                    conversationHistory.push({
                        role: 'assistant',
                        content: data.response,
                        timestamp: new Date()
                    });
                    
                    // Play audio response if available
                    if (data.audio_url) {
                        playAudioResponse(data.audio_url);
                    }
                }
            } else {
                // Show error message
                addSystemMessage(data.error || 'Error processing speech. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error processing speech:', error);
            addSystemMessage('Error communicating with server. Please try again.');
        })
        .finally(() => {
            // Reset processing state
            isProcessing = false;
            document.getElementById('status-text').textContent = 'Ready';
        });
    }

    /**
     * Play audio response and synchronize with avatar
     */
    function playAudioResponse(audioUrl) {
        // Start avatar video
        startAvatarVideo();
        
        // Play audio
        const audio = audioProcessor.playAudio(
            audioUrl,
            () => {
                // Audio started playing
                document.getElementById('status-text').textContent = 'Speaking...';
            },
            () => {
                // Audio finished playing
                document.getElementById('status-text').textContent = 'Ready';
                pauseAvatarVideo();
            }
        );
    }

    /**
     * Start avatar video playback
     */
    function startAvatarVideo() {
        if (videoSync) {
            videoSync.play();
        }
    }

    /**
     * Pause avatar video playback
     */
    function pauseAvatarVideo() {
        if (videoSync) {
            videoSync.pause();
        }
    }

    /**
     * Visualize audio input in real-time
     */
    let visualizationAnimationFrame = null;
    function visualizeAudio() {
        if (!audioProcessor.isCurrentlyRecording()) {
            cancelAnimationFrame(visualizationAnimationFrame);
            return;
        }
        
        // Get frequency data
        const frequencyData = audioProcessor.getFrequencyData();
        
        if (frequencyData) {
            // Get audio wave elements
            const waveElements = document.querySelectorAll('.audio-wave span');
            
            // Update heights based on frequency data
            // Using a simple algorithm to map frequency data to visual elements
            // This could be made more sophisticated
            const step = Math.floor(frequencyData.length / waveElements.length);
            waveElements.forEach((element, index) => {
                const frequencyValue = frequencyData[index * step];
                const height = Math.max(5, (frequencyValue / 255) * 30);
                element.style.height = `${height}px`;
            });
        }
        
        // Continue animation
        visualizationAnimationFrame = requestAnimationFrame(visualizeAudio);
    }

    /**
     * Add a user message to the conversation
     */
    function addUserMessage(text, id, timestamp) {
        const messagesContainer = document.querySelector('.conversation-messages');
        const formattedTime = formatTimestamp(timestamp);
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        messageElement.id = id;
        
        messageElement.innerHTML = `
            <div class="message-bubble">
                <div class="message-content">${text}</div>
            </div>
            <div class="message-info">
                <span class="message-time">${formattedTime}</span>
                <span class="message-agent">You</span>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        scrollToBottom();
    }

    /**
     * Update an existing user message
     */
    function updateUserMessage(id, text) {
        const messageElement = document.getElementById(id);
        if (messageElement) {
            const contentElement = messageElement.querySelector('.message-content');
            if (contentElement) {
                contentElement.textContent = text;
            }
        }
    }

    /**
     * Add an AI message to the conversation
     */
    function addAIMessage(text, timestamp) {
        const messagesContainer = document.querySelector('.conversation-messages');
        const formattedTime = formatTimestamp(timestamp);
        const toolData = aiTools.getCurrentToolData();
        const agentName = toolData?.name || 'INNOVATE AI';
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message ai-message';
        
        messageElement.innerHTML = `
            <div class="message-bubble">
                <div class="message-content">${text}</div>
            </div>
            <div class="message-info">
                <span class="message-time">${formattedTime}</span>
                <span class="message-agent">${agentName}</span>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        scrollToBottom();
    }

    /**
     * Add a system message to the conversation
     */
    function addSystemMessage(text) {
        const messagesContainer = document.querySelector('.conversation-messages');
        const formattedTime = formatTimestamp(new Date());
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message system-message';
        
        messageElement.innerHTML = `
            <div class="message-bubble">
                <div class="message-content">${text}</div>
            </div>
            <div class="message-info">
                <span class="message-time">${formattedTime}</span>
                <span class="message-agent">System</span>
            </div>
        `;
        
        messagesContainer.appendChild(messageElement);
        scrollToBottom();
    }

    /**
     * Format timestamp for display
     */
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    /**
     * Scroll the conversation to the bottom
     */
    function scrollToBottom() {
        const messagesContainer = document.querySelector('.conversation-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Clear the conversation history
     */
    function clearConversation() {
        // Clear conversation history
        conversationHistory = [];
        
        // Clear conversation UI
        const messagesContainer = document.querySelector('.conversation-messages');
        messagesContainer.innerHTML = '';
        
        // Show initial system message
        addSystemMessage('Conversation cleared. Start a new conversation by clicking the microphone button.');
    }
});