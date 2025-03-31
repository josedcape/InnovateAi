/**
 * INNOVATE AI - AI Tools Module
 * Manages interactions with different AI tools (web search, computer use, file search)
 */

class AITools {
    constructor() {
        this.currentTool = 'default'; // Default tool
        this.tools = {}; // Will be populated when loaded from server
        this.fileUploadSection = null;
    }

    /**
     * Initialize tools UI and functionality
     */
    initTools() {
        // Get tools data from server
        fetch('/get_agents')
            .then(response => response.json())
            .then(data => {
                this.tools = data;
                this.renderTools();
                this.initFileUpload();
                this.loadFiles();
            })
            .catch(error => {
                console.error('Error loading tools:', error);
            });
            
        // Initialize file upload section reference
        this.fileUploadSection = document.getElementById('file-upload-section');
    }

    /**
     * Render tools UI from loaded data
     */
    renderTools() {
        const toolsGrid = document.getElementById('tools-grid');
        if (!toolsGrid) return;
        
        // Create tool cards
        Object.values(this.tools).forEach(tool => {
            const toolCard = document.createElement('div');
            toolCard.className = 'tool-card';
            toolCard.setAttribute('data-tool', tool.type);
            
            // Create HTML structure for tool card
            toolCard.innerHTML = `
                <div class="tool-icon">
                    <img src="${tool.icon || '/static/icons/default-icon.svg'}" alt="${tool.name} icon" width="24" height="24">
                </div>
                <div class="tool-info">
                    <h4>${tool.name}</h4>
                    <p>${tool.description}</p>
                </div>
            `;
            
            // Add click event listener
            toolCard.addEventListener('click', () => {
                this.selectTool(tool.type);
            });
            
            toolsGrid.appendChild(toolCard);
        });
        
        // Select default tool
        this.selectTool('default');
    }

    /**
     * Initialize file upload functionality
     */
    initFileUpload() {
        const fileInput = document.getElementById('file-upload');
        const fileNameDisplay = document.getElementById('file-name');
        const uploadButton = document.getElementById('upload-btn');
        
        if (!fileInput || !fileNameDisplay || !uploadButton) return;
        
        // Show file name when selected
        fileInput.addEventListener('change', (event) => {
            if (event.target.files.length > 0) {
                fileNameDisplay.textContent = event.target.files[0].name;
                document.getElementById('upload-submit-btn').disabled = false;
            } else {
                fileNameDisplay.textContent = 'No file selected';
                document.getElementById('upload-submit-btn').disabled = true;
            }
        });
        
        // Upload button functionality
        uploadButton.addEventListener('click', () => {
            fileInput.click();
        });
        
        // Submit button functionality
        document.getElementById('upload-submit-btn').addEventListener('click', () => {
            this.uploadFile();
        });
    }

    /**
     * Select a tool to use
     * @param {string} toolType Tool identifier
     */
    selectTool(toolType) {
        // Nothing to do if same tool already selected
        if (this.currentTool === toolType) return;
        
        // Update current tool
        this.currentTool = toolType;
        
        // Remove active class from all tools
        const toolCards = document.querySelectorAll('.tool-card');
        toolCards.forEach(card => card.classList.remove('active'));
        
        // Add active class to selected tool
        const selectedCard = document.querySelector(`.tool-card[data-tool="${toolType}"]`);
        if (selectedCard) {
            selectedCard.classList.add('active');
        }
        
        // Update UI based on selected tool
        this.updateFileUploadVisibility();
        
        // Update status text to reflect selected tool
        const statusText = document.getElementById('status-text');
        if (statusText) {
            const toolData = this.getCurrentToolData();
            statusText.textContent = `Ready to use ${toolData?.name || 'AI Assistant'}`;
        }
        
        console.log(`Selected tool: ${toolType}`);
    }

    /**
     * Get the currently selected tool
     * @returns {string} Tool identifier
     */
    getCurrentTool() {
        return this.currentTool;
    }

    /**
     * Get details about the currently selected tool
     * @returns {Object} Tool data
     */
    getCurrentToolData() {
        return this.tools[this.currentTool] || null;
    }

    /**
     * Update file upload section visibility based on selected tool
     */
    updateFileUploadVisibility() {
        if (!this.fileUploadSection) return;
        
        // Show file upload section only for file_search tool
        if (this.currentTool === 'file_search') {
            this.fileUploadSection.style.display = 'block';
        } else {
            this.fileUploadSection.style.display = 'none';
        }
    }

    /**
     * Upload a file to the server
     */
    uploadFile() {
        const fileInput = document.getElementById('file-upload');
        if (!fileInput || !fileInput.files.length) {
            this.showFileUploadError('Please select a file to upload.');
            return;
        }
        
        const file = fileInput.files[0];
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        
        // Show loading state
        document.getElementById('upload-submit-btn').disabled = true;
        document.getElementById('upload-submit-btn').textContent = 'Uploading...';
        
        // Send file to server
        fetch('/upload_file', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reset file input
                fileInput.value = '';
                document.getElementById('file-name').textContent = 'No file selected';
                
                // Show success message
                this.showFileUploadSuccess(data.message || 'File uploaded successfully.');
                
                // Refresh file list
                this.loadFiles();
            } else {
                this.showFileUploadError(data.error || 'Failed to upload file.');
            }
        })
        .catch(error => {
            console.error('Error uploading file:', error);
            this.showFileUploadError('Error uploading file. Please try again.');
        })
        .finally(() => {
            // Reset button state
            document.getElementById('upload-submit-btn').textContent = 'Upload';
            document.getElementById('upload-submit-btn').disabled = false;
        });
    }

    /**
     * Load list of uploaded files
     */
    loadFiles() {
        const fileList = document.getElementById('file-list');
        if (!fileList) return;
        
        // Show loading state
        fileList.innerHTML = '<li>Loading files...</li>';
        
        // Get files from server
        fetch('/get_files')
            .then(response => response.json())
            .then(data => {
                if (data.files && data.files.length > 0) {
                    // Clear list
                    fileList.innerHTML = '';
                    
                    // Add each file to list
                    data.files.forEach(file => {
                        const li = document.createElement('li');
                        li.innerHTML = `<i class="fa fa-file"></i> ${file.filename} <small>(${this.formatFileSize(file.size_bytes)})</small>`;
                        fileList.appendChild(li);
                    });
                } else {
                    // Show empty message
                    fileList.innerHTML = '<li class="empty-message">No files uploaded yet.</li>';
                }
            })
            .catch(error => {
                console.error('Error loading files:', error);
                fileList.innerHTML = '<li class="empty-message">Error loading files.</li>';
            });
    }

    /**
     * Format file size in human-readable format
     * @param {number} bytes File size in bytes
     * @returns {string} Formatted file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Show a file upload success message
     * @param {string} message Success message to show
     */
    showFileUploadSuccess(message) {
        const alert = document.createElement('div');
        alert.className = 'file-upload-alert success';
        alert.textContent = message;
        
        this.showFileUploadAlert(alert);
    }

    /**
     * Show a file upload error message
     * @param {string} message Error message to show
     */
    showFileUploadError(message) {
        const alert = document.createElement('div');
        alert.className = 'file-upload-alert error';
        alert.textContent = message;
        
        this.showFileUploadAlert(alert);
    }

    /**
     * Show a file upload alert
     * @param {HTMLElement} alertElement Alert element to show
     */
    showFileUploadAlert(alertElement) {
        const container = document.getElementById('file-upload-alerts');
        if (!container) return;
        
        // Add alert to container
        container.appendChild(alertElement);
        
        // Remove alert after 5 seconds
        setTimeout(() => {
            alertElement.remove();
        }, 5000);
    }
}