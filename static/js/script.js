/**
 * INNOVATE AI - Main Application Script
 * Handles core UI interactions, conversation management, and tool switching
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize modules
    const audioProcessor = new AudioProcessor();
    const aiTools = new AITools();
    let videoSync;
    
    // Initialize UI
    initializeUI();
    
    // Initialize text input
    const textInput = document.getElementById('text-input');
    const sendButton = document.getElementById('send-button');
    
    if (textInput && sendButton) {
        // Send on Enter key press
        textInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendTextMessage();
            }
        });
        
        // Send on button click
        sendButton.addEventListener('click', sendTextMessage);
    }
    
    /**
     * Initialize the user interface and components
     */
    function initializeUI() {
        // Initialize audio processor
        audioProcessor.initialize()
            .then(() => {
                console.log('Audio processor initialized');
            })
            .catch(error => {
                console.error('Failed to initialize audio processor:', error);
                addSystemMessage('Error initializing audio. Please check microphone permissions.');
            });
        
        // Initialize avatar video
        initializeAvatarVideo();
        
        // Initialize AI tools
        aiTools.initTools();
        
        // Set up recording button
        const recordButton = document.getElementById('record-button');
        if (recordButton) {
            recordButton.addEventListener('click', toggleRecording);
        }
        
        // Set up clear conversation button
        const clearButton = document.querySelector('.clear-button');
        if (clearButton) {
            clearButton.addEventListener('click', clearConversation);
        }
        
        // Add welcome message
        addSystemMessage('Welcome to INNOVATE AI! Click the microphone button to start speaking, or switch between different AI capabilities using the tools above.');
        
        // Start visualization
        visualizeAudio();
    }
    
    /**
     * Initialize the avatar video element
     */
    function initializeAvatarVideo() {
        const videoElement = document.getElementById('avatar-video');
        if (videoElement) {
            videoSync = new VideoSync(videoElement);
            console.log('Avatar video initialized');
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
        const recordButton = document.getElementById('record-button');
        const statusMessage = document.querySelector('.status-message');
        
        // Update UI
        recordButton.classList.add('recording');
        recordButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white">
                <rect x="6" y="6" width="12" height="12" rx="2" />
            </svg>
        `;
        statusMessage.textContent = 'Listening...';
        
        // Add user message placeholder
        const messageId = 'message-' + Date.now();
        addUserMessage('...', messageId, new Date());
        
        // Start recording
        audioProcessor.startRecording(
            // Data available callback
            (data) => {
                // This is fired when data is available but recording is still ongoing
            },
            // Complete callback
            (audioBlob) => {
                processAudioRecording(audioBlob, messageId);
            }
        ).catch(error => {
            console.error('Error starting recording:', error);
            addSystemMessage('Error accessing microphone. Please check permissions.');
            stopRecording();
        });
    }
    
    /**
     * Stop recording audio
     */
    function stopRecording() {
        const recordButton = document.getElementById('record-button');
        const statusMessage = document.querySelector('.status-message');
        
        // Update UI
        recordButton.classList.remove('recording');
        recordButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white">
                <path d="M12 15c1.66 0 3-1.34 3-3V6c0-1.66-1.34-3-3-3S9 4.34 9 6v6c0 1.66 1.34 3 3 3z" />
                <path d="M17 12c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-2.08c3.39-.49 6-3.39 6-6.92h-2z" />
            </svg>
        `;
        statusMessage.textContent = 'Processing...';
        
        // Stop recording
        audioProcessor.stopRecording();
    }
    
    /**
     * Process the recorded audio
     */
    function processAudioRecording(audioBlob, messageId) {
        const statusMessage = document.querySelector('.status-message');
        const loadingIndicator = document.querySelector('.loading-indicator');
        
        // Show loading indicator
        loadingIndicator.style.display = 'flex';
        
        // Create form data for API request
        const formData = new FormData();
        formData.append('audio', audioBlob);
        
        // Add selected agent type
        const selectedTool = aiTools.getCurrentTool();
        formData.append('agent_type', selectedTool);
        
        // Start a 5-second countdown before sending to assistant
        const countdownTimer = document.querySelector('.countdown-timer');
        countdownTimer.textContent = '5';
        countdownTimer.classList.remove('hidden');
        
        let countdown = 5;
        const countdownInterval = setInterval(() => {
            countdown--;
            countdownTimer.textContent = countdown;
            
            if (countdown <= 0) {
                clearInterval(countdownInterval);
                countdownTimer.classList.add('hidden');
                
                // Send the audio to the server
                fetch('/api/speech', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    // Hide loading indicator
                    loadingIndicator.style.display = 'none';
                    
                    // Update status
                    statusMessage.textContent = 'Ready';
                    
                    if (data.error) {
                        console.error('Error processing speech:', data.error);
                        addSystemMessage(`Error: ${data.error}`);
                        return;
                    }
                    
                    // Update user message with transcription
                    updateUserMessage(messageId, data.transcript);
                    
                    // Add AI response
                    addAIMessage(data.response, new Date());
                    
                    // Play audio response
                    if (data.audio_url) {
                        playAudioResponse(data.audio_url);
                    }
                })
                .catch(error => {
                    // Hide loading indicator
                    loadingIndicator.style.display = 'none';
                    
                    // Update status
                    statusMessage.textContent = 'Ready';
                    
                    console.error('Error sending audio to server:', error);
                    addSystemMessage('Error communicating with the server. Please try again.');
                });
            }
        }, 1000);
    }
    
    /**
     * Play audio response and synchronize with avatar
     */
    function playAudioResponse(audioUrl) {
        // Start avatar animation
        if (videoSync) {
            startAvatarVideo();
        }
        
        // Play audio
        const audio = audioProcessor.playAudio(
            audioUrl,
            // Play callback
            () => {
                console.log('Audio started playing');
            },
            // End callback
            () => {
                console.log('Audio finished playing');
                // Stop avatar animation
                if (videoSync) {
                    pauseAvatarVideo();
                }
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
    function visualizeAudio() {
        const visualizationBars = document.querySelectorAll('.visualization-bar');
        
        // If we don't have visualization bars, create them
        if (visualizationBars.length === 0) {
            const visualizationContainer = document.querySelector('.visualization-bars');
            if (visualizationContainer) {
                for (let i = 0; i < 50; i++) {
                    const bar = document.createElement('div');
                    bar.className = 'visualization-bar';
                    visualizationContainer.appendChild(bar);
                }
            }
        }
        
        function updateVisualization() {
            // Get frequency data
            const frequencyData = audioProcessor.getFrequencyData();
            const bars = document.querySelectorAll('.visualization-bar');
            
            if (frequencyData && bars.length > 0) {
                // The number of frequency bins may be different than the number of bars
                // so we need to sample the frequency data
                const step = Math.floor(frequencyData.length / bars.length);
                
                // Scale the visualization based on recording state
                const scaleFactor = audioProcessor.isCurrentlyRecording() ? 1.0 : 0.3;
                
                for (let i = 0; i < bars.length; i++) {
                    const frequencyIndex = Math.min(i * step, frequencyData.length - 1);
                    let value = frequencyData[frequencyIndex];
                    
                    // Scale the value to a reasonable height (0-48px)
                    value = value * scaleFactor * 0.5;
                    
                    // Add some minimum height for aesthetics
                    const height = Math.max(5, value);
                    
                    bars[i].style.height = `${height}px`;
                }
            }
            
            // Continue visualization
            requestAnimationFrame(updateVisualization);
        }
        
        // Start the visualization loop
        updateVisualization();
    }
    
    /**
     * Add a user message to the conversation
     */
    function addUserMessage(text, id, timestamp) {
        addMessage('user', text, id, timestamp);
        scrollToBottom();
    }
    
    /**
     * Update an existing user message
     */
    function updateUserMessage(id, text) {
        const messageContent = document.querySelector(`#${id} .message-content`);
        if (messageContent) {
            messageContent.textContent = text;
            scrollToBottom();
        }
    }
    
    /**
     * Add an AI message to the conversation
     */
    function addAIMessage(text, timestamp) {
        addMessage('assistant', text, null, timestamp);
        scrollToBottom();
    }
    
    /**
     * Add a system message to the conversation
     */
    function addSystemMessage(text) {
        const conversationContainer = document.querySelector('.conversation-container');
        
        if (!conversationContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = text;
        
        messageDiv.appendChild(messageContent);
        conversationContainer.appendChild(messageDiv);
        
        scrollToBottom();
    }
    
    /**
     * Add a message to the conversation
     */
    function addMessage(role, text, id, timestamp) {
        const conversationContainer = document.querySelector('.conversation-container');
        
        if (!conversationContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;
        if (id) {
            messageDiv.id = id;
        }
        
        // Create avatar and sender info
        const messageHeader = document.createElement('div');
        messageHeader.className = 'message-header';
        
        const messageAvatar = document.createElement('div');
        messageAvatar.className = `message-avatar ${role}-avatar`;
        messageAvatar.textContent = role === 'user' ? 'U' : 'AI';
        
        const messageMeta = document.createElement('div');
        messageMeta.className = 'message-meta';
        
        const messageSender = document.createElement('div');
        messageSender.className = 'message-sender';
        messageSender.textContent = role === 'user' ? 'You' : 'INNOVATE AI';
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = formatTimestamp(timestamp);
        
        messageMeta.appendChild(messageSender);
        messageMeta.appendChild(messageTime);
        
        messageHeader.appendChild(messageAvatar);
        messageHeader.appendChild(messageMeta);
        
        // Add message actions for AI messages (copy, stop audio)
        if (role === 'assistant') {
            const messageActions = document.createElement('div');
            messageActions.className = 'message-actions';
            
            // Copy message button
            const copyButton = document.createElement('button');
            copyButton.className = 'action-button copy-button';
            copyButton.innerHTML = '<i class="fas fa-copy"></i>';
            copyButton.title = 'Copy to clipboard';
            copyButton.addEventListener('click', function() {
                copyToClipboard(text);
                
                // Show feedback
                const originalHTML = copyButton.innerHTML;
                copyButton.innerHTML = '<i class="fas fa-check"></i>';
                copyButton.classList.add('copied');
                
                setTimeout(() => {
                    copyButton.innerHTML = originalHTML;
                    copyButton.classList.remove('copied');
                }, 2000);
            });
            
            // Stop audio button
            const stopAudioButton = document.createElement('button');
            stopAudioButton.className = 'action-button stop-audio-button';
            stopAudioButton.innerHTML = '<i class="fas fa-volume-mute"></i>';
            stopAudioButton.title = 'Stop audio playback';
            stopAudioButton.addEventListener('click', function() {
                // Stop any currently playing audio
                if (audioProcessor.currentAudio) {
                    audioProcessor.currentAudio.pause();
                    audioProcessor.currentAudio = null;
                    
                    // Also pause the avatar video
                    pauseAvatarVideo();
                }
            });
            
            messageActions.appendChild(copyButton);
            messageActions.appendChild(stopAudioButton);
            messageHeader.appendChild(messageActions);
        }
        
        // Create message content
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = text;
        
        messageDiv.appendChild(messageHeader);
        messageDiv.appendChild(messageContent);
        
        conversationContainer.appendChild(messageDiv);
    }
    
    /**
     * Copy text to clipboard
     */
    function copyToClipboard(text) {
        // Create a temporary textarea element
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.setAttribute('readonly', '');
        textarea.style.position = 'absolute';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        
        // Select and copy the text
        textarea.select();
        document.execCommand('copy');
        
        // Clean up
        document.body.removeChild(textarea);
    }
    
    /**
     * Format timestamp for display
     */
    function formatTimestamp(timestamp) {
        if (!timestamp) return '';
        
        return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    /**
     * Scroll the conversation to the bottom
     */
    function scrollToBottom() {
        const conversationContainer = document.querySelector('.conversation-container');
        if (conversationContainer) {
            conversationContainer.scrollTop = conversationContainer.scrollHeight;
        }
    }
    
    /**
     * Send a text message
     */
    function sendTextMessage() {
        const textInput = document.getElementById('text-input');
        const text = textInput.value.trim();
        
        if (!text) return;
        
        // Clear input field
        textInput.value = '';
        
        // Add user message to conversation
        const messageId = 'msg-' + Date.now();
        addUserMessage(text, messageId, new Date());
        
        // Show loading indicator
        const loadingIndicator = document.querySelector('.loading-indicator');
        loadingIndicator.style.display = 'flex';
        
        // Update status message
        const statusMessage = document.querySelector('.status-message');
        statusMessage.textContent = 'Processing your message...';
        
        // Send the text to the server
        fetch('/api/speech', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                agent_type: aiTools.getCurrentTool()
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
            
            // Update status
            statusMessage.textContent = 'Ready';
            
            if (data.error) {
                console.error('Error processing text:', data.error);
                addSystemMessage(`Error: ${data.error}`);
                return;
            }
            
            // Add AI response
            addAIMessage(data.response, new Date());
            
            // Play audio response
            if (data.audio_url) {
                playAudioResponse(data.audio_url);
            }
        })
        .catch(error => {
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
            
            // Update status
            statusMessage.textContent = 'Ready';
            
            console.error('Error sending text to server:', error);
            addSystemMessage('Error communicating with the server. Please try again.');
        });
    }
    
    /**
     * Clear the conversation history
     */
    function clearConversation() {
        const conversationContainer = document.querySelector('.conversation-container');
        if (conversationContainer) {
            // Remove all messages except the welcome message
            const messages = conversationContainer.querySelectorAll('.message:not(.system-message)');
            messages.forEach(message => message.remove());
            
            // Add a system message indicating conversation was cleared
            addSystemMessage('Conversation history cleared.');
        }
    }
});