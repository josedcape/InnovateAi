/**
 * INNOVATE AI - AI Tools Module
 * Manages interactions with different AI tools (web search, computer use, file search)
 */

class AITools {
    constructor() {
        this.tools = [];
        this.selectedTool = 'default';
        this.toolsContainer = null;
        this.fileUploadContainer = null;
    }
    
    /**
     * Initialize tools UI and functionality
     */
    initTools() {
        this.toolsContainer = document.querySelector('.tools-container');
        this.fileUploadContainer = document.querySelector('.file-upload-container');
        
        // Fetch available tools from API
        fetch('/api/agents')
            .then(response => response.json())
            .then(agents => {
                this.tools = agents;
                this.renderTools();
            })
            .catch(error => {
                console.error('Error fetching agents:', error);
                // Add default tool if API fails
                this.tools = [{
                    name: 'Standard Assistant',
                    type: 'default',
                    description: 'General-purpose AI assistant with conversation capabilities',
                    icon: '/static/icons/search-icon.svg'
                }];
                this.renderTools();
            });
        
        // Initialize file upload
        this.initFileUpload();
    }
    
    /**
     * Render tools UI from loaded data
     */
    renderTools() {
        // Clear container
        this.toolsContainer.innerHTML = '';
        
        // Create tool buttons
        this.tools.forEach(tool => {
            const toolButton = document.createElement('button');
            toolButton.className = 'tool-button';
            toolButton.dataset.toolType = tool.type;
            
            if (tool.type === this.selectedTool) {
                toolButton.classList.add('active');
            }
            
            // Use Font Awesome icons instead of SVG images
            let iconClass = 'fas fa-robot'; // Default icon
            
            // Set specific icons based on tool type
            if (tool.type === 'web_search') {
                iconClass = 'fas fa-search-plus';
            } else if (tool.type === 'computer_use') {
                iconClass = 'fas fa-laptop-code';
            } else if (tool.type === 'file_search') {
                iconClass = 'fas fa-file-search';
            } else if (tool.type === 'default') {
                iconClass = 'fas fa-robot';
            }
            
            toolButton.innerHTML = `
                <i class="${iconClass} tool-icon"></i>
                <span class="tool-label">${tool.name}</span>
            `;
            
            toolButton.addEventListener('click', () => {
                this.selectTool(tool.type);
            });
            
            this.toolsContainer.appendChild(toolButton);
        });
        
        // Update file upload visibility
        this.updateFileUploadVisibility();
    }
    
    /**
     * Initialize file upload functionality
     */
    initFileUpload() {
        const fileInput = document.getElementById('file-upload');
        const uploadButton = document.querySelector('.file-upload-button');
        const successAlert = document.querySelector('.file-upload-success');
        const errorAlert = document.querySelector('.file-upload-error');
        
        if (!fileInput || !uploadButton) return;
        
        uploadButton.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                this.uploadFile();
            }
        });
        
        // Load existing files
        this.loadFiles();
    }
    
    /**
     * Select a tool to use
     * @param {string} toolType Tool identifier
     */
    selectTool(toolType) {
        this.selectedTool = toolType;
        
        // Update UI to reflect selection
        const toolButtons = this.toolsContainer.querySelectorAll('.tool-button');
        toolButtons.forEach(button => {
            if (button.dataset.toolType === toolType) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
        
        // Update file upload visibility
        this.updateFileUploadVisibility();
        
        // Add animation effect
        const activeButton = this.toolsContainer.querySelector(`.tool-button[data-tool-type="${toolType}"]`);
        if (activeButton) {
            activeButton.animate(
                [
                    { transform: 'scale(0.95)', opacity: 0.8 },
                    { transform: 'scale(1.05)', opacity: 1 },
                    { transform: 'scale(1)', opacity: 1 }
                ],
                { duration: 300, easing: 'ease-out' }
            );
        }
    }
    
    /**
     * Get the currently selected tool
     * @returns {string} Tool identifier
     */
    getCurrentTool() {
        return this.selectedTool;
    }
    
    /**
     * Get details about the currently selected tool
     * @returns {Object} Tool data
     */
    getCurrentToolData() {
        return this.tools.find(tool => tool.type === this.selectedTool);
    }
    
    /**
     * Update file upload section visibility based on selected tool
     */
    updateFileUploadVisibility() {
        if (this.fileUploadContainer) {
            if (this.selectedTool === 'file_search') {
                this.fileUploadContainer.style.display = 'flex';
            } else {
                this.fileUploadContainer.style.display = 'none';
            }
        }
    }
    
    /**
     * Upload a file to the server
     */
    uploadFile() {
        const fileInput = document.getElementById('file-upload');
        const successAlert = document.querySelector('.file-upload-success');
        const errorAlert = document.querySelector('.file-upload-error');
        
        if (!fileInput.files.length) return;
        
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);
        
        // Hide previous alerts
        successAlert.style.display = 'none';
        errorAlert.style.display = 'none';
        
        // Upload file
        fetch('/api/upload-file', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success message
                this.showFileUploadSuccess(`File "${file.name}" uploaded successfully!`);
                // Reset file input
                fileInput.value = '';
                // Reload file list
                this.loadFiles();
            } else {
                // Show error message
                this.showFileUploadError(data.error || 'Error uploading file');
            }
        })
        .catch(error => {
            console.error('Error uploading file:', error);
            this.showFileUploadError('Error uploading file: Network error');
        });
    }
    
    /**
     * Load list of uploaded files
     */
    loadFiles() {
        const fileList = document.querySelector('.file-list');
        
        if (!fileList) return;
        
        fetch('/api/files')
            .then(response => response.json())
            .then(data => {
                fileList.innerHTML = '';
                
                if (data.files && data.files.length > 0) {
                    data.files.forEach(file => {
                        const fileItem = document.createElement('div');
                        fileItem.className = 'file-item';
                        fileItem.innerHTML = `
                            <span>${file.filename}</span>
                            <span>${this.formatFileSize(file.bytes)}</span>
                        `;
                        fileList.appendChild(fileItem);
                    });
                } else {
                    fileList.innerHTML = '<div class="file-item">No files uploaded yet</div>';
                }
            })
            .catch(error => {
                console.error('Error loading files:', error);
                fileList.innerHTML = '<div class="file-item">Error loading files</div>';
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
        const successAlert = document.querySelector('.file-upload-success');
        successAlert.textContent = message;
        this.showFileUploadAlert(successAlert);
    }
    
    /**
     * Show a file upload error message
     * @param {string} message Error message to show
     */
    showFileUploadError(message) {
        const errorAlert = document.querySelector('.file-upload-error');
        errorAlert.textContent = message;
        this.showFileUploadAlert(errorAlert);
    }
    
    /**
     * Show a file upload alert
     * @param {HTMLElement} alertElement Alert element to show
     */
    showFileUploadAlert(alertElement) {
        // Hide all alerts first
        document.querySelectorAll('.file-upload-alert').forEach(alert => {
            alert.style.display = 'none';
        });
        
        // Show the specified alert
        alertElement.style.display = 'block';
        
        // Animate the alert
        alertElement.animate(
            [
                { opacity: 0, transform: 'translateY(-10px)' },
                { opacity: 1, transform: 'translateY(0)' }
            ],
            { duration: 300, easing: 'ease-out' }
        );
        
        // Hide after 5 seconds
        setTimeout(() => {
            alertElement.animate(
                [
                    { opacity: 1 },
                    { opacity: 0 }
                ],
                { duration: 300, easing: 'ease-out' }
            ).onfinish = () => {
                alertElement.style.display = 'none';
            };
        }, 5000);
    }
}