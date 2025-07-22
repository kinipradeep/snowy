// Contact Manager JavaScript

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeFeatherIcons();
    initializeTooltips();
    initializeFormValidation();
    initializeSearchFunctionality();
    initializeKeyboardShortcuts();
});

// Initialize Feather Icons
function initializeFeatherIcons() {
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Form validation enhancements
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

// Search functionality
function initializeSearchFunctionality() {
    const searchInputs = document.querySelectorAll('input[type="search"], input[name="search"]');
    
    searchInputs.forEach(function(input) {
        input.addEventListener('input', debounce(function(e) {
            const searchTerm = e.target.value.trim();
            if (searchTerm.length >= 2) {
                // Highlight search terms in results (if results are on the same page)
                highlightSearchTerms(searchTerm);
            } else {
                clearHighlights();
            }
        }, 300));
    });
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Highlight search terms
function highlightSearchTerms(term) {
    const elements = document.querySelectorAll('.list-group-item, .card-body');
    const regex = new RegExp(`(${term})`, 'gi');
    
    elements.forEach(function(element) {
        const originalText = element.getAttribute('data-original-text') || element.innerHTML;
        if (!element.getAttribute('data-original-text')) {
            element.setAttribute('data-original-text', originalText);
        }
        
        element.innerHTML = originalText.replace(regex, '<mark>$1</mark>');
    });
}

// Clear search highlights
function clearHighlights() {
    const elements = document.querySelectorAll('[data-original-text]');
    elements.forEach(function(element) {
        element.innerHTML = element.getAttribute('data-original-text');
        element.removeAttribute('data-original-text');
    });
}

// Keyboard shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Only trigger shortcuts when not in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // Ctrl/Cmd + N for new items
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newButtons = document.querySelectorAll('[href*="/new"]');
            if (newButtons.length > 0) {
                newButtons[0].click();
            }
        }
        
        // ESC to close modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(function(modal) {
                bootstrap.Modal.getInstance(modal).hide();
            });
        }
        
        // / to focus search
        if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"], input[name="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
    });
}

// Contact form enhancements
function setupContactForm() {
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            formatPhoneNumber(e.target);
        });
    });
}

// Format phone number
function formatPhoneNumber(input) {
    let value = input.value.replace(/\D/g, '');
    
    if (value.length >= 6) {
        if (value.length === 10) {
            value = value.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
        } else if (value.length === 11 && value[0] === '1') {
            value = value.replace(/(\d{1})(\d{3})(\d{3})(\d{4})/, '+$1 ($2) $3-$4');
        }
    }
    
    input.value = value;
}

// Show loading state on buttons
function showButtonLoading(button, loadingText = 'Loading...') {
    if (button.getAttribute('data-original-text')) {
        return; // Already in loading state
    }
    
    button.setAttribute('data-original-text', button.innerHTML);
    button.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span>${loadingText}`;
    button.disabled = true;
}

// Hide loading state on buttons
function hideButtonLoading(button) {
    const originalText = button.getAttribute('data-original-text');
    if (originalText) {
        button.innerHTML = originalText;
        button.removeAttribute('data-original-text');
        button.disabled = false;
    }
}

// Form submission with loading states
function setupFormSubmission() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && !form.classList.contains('no-loading')) {
                showButtonLoading(submitButton, 'Saving...');
                
                // Hide loading state if form validation fails
                setTimeout(function() {
                    if (form.classList.contains('was-validated') && !form.checkValidity()) {
                        hideButtonLoading(submitButton);
                    }
                }, 100);
            }
        });
    });
}

// Auto-resize textarea
function setupAutoResizeTextarea() {
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
        
        // Initial resize
        textarea.style.height = textarea.scrollHeight + 'px';
    });
}

// Confirm delete actions
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

// Copy text to clipboard
function copyToClipboard(text, successMessage = 'Copied to clipboard!') {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showNotification(successMessage, 'success');
        }).catch(function() {
            fallbackCopyToClipboard(text, successMessage);
        });
    } else {
        fallbackCopyToClipboard(text, successMessage);
    }
}

// Fallback copy to clipboard
function fallbackCopyToClipboard(text, successMessage) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showNotification(successMessage, 'success');
    } catch (err) {
        console.error('Failed to copy text: ', err);
        showNotification('Failed to copy text', 'error');
    }
    
    document.body.removeChild(textArea);
}

// Show notification
function showNotification(message, type = 'info', duration = 3000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto remove after duration
    setTimeout(function() {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// Initialize all enhancements
document.addEventListener('DOMContentLoaded', function() {
    setupContactForm();
    setupFormSubmission();
    setupAutoResizeTextarea();
});

// Utility functions for templates
const TemplateUtils = {
    insertVariable: function(variableName, targetFieldId = 'content') {
        const field = document.getElementById(targetFieldId);
        if (!field) return;
        
        const cursorPos = field.selectionStart;
        const textBefore = field.value.substring(0, cursorPos);
        const textAfter = field.value.substring(cursorPos);
        
        field.value = textBefore + '{' + variableName + '}' + textAfter;
        
        // Set cursor position after the inserted variable
        const newCursorPos = cursorPos + variableName.length + 2;
        field.setSelectionRange(newCursorPos, newCursorPos);
        field.focus();
    },
    
    previewTemplate: function(content, variables = {}) {
        let preview = content;
        Object.keys(variables).forEach(function(key) {
            const regex = new RegExp('\\{' + key + '\\}', 'g');
            preview = preview.replace(regex, variables[key]);
        });
        return preview;
    }
};

// Export for use in other scripts
// Messaging Dashboard Functions
function showSendMessageModal() {
    // Create a modal for sending single messages
    const modalHtml = `
        <div class="modal fade" id="sendMessageModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content bg-dark">
                    <div class="modal-header border-secondary">
                        <h5 class="modal-title text-light">
                            <i data-feather="message-circle" width="20" height="20" class="me-2"></i>
                            Send Message
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form>
                            <div class="mb-3">
                                <label class="form-label text-light">Message Type</label>
                                <select class="form-select bg-secondary text-light border-secondary">
                                    <option value="sms">SMS</option>
                                    <option value="email">Email</option>
                                    <option value="whatsapp">WhatsApp</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">Recipient</label>
                                <input type="text" class="form-control bg-secondary text-light border-secondary" placeholder="Enter phone/email">
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">Message</label>
                                <textarea class="form-control bg-secondary text-light border-secondary" rows="4" placeholder="Type your message..."></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer border-secondary">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary">Send Message</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('sendMessageModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body and show
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('sendMessageModal'));
    modal.show();
    
    // Reinitialize feather icons for the modal
    setTimeout(() => feather.replace(), 100);
}

function showBulkMessageModal() {
    const modalHtml = `
        <div class="modal fade" id="bulkMessageModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content bg-dark">
                    <div class="modal-header border-secondary">
                        <h5 class="modal-title text-light">
                            <i data-feather="users" width="20" height="20" class="me-2"></i>
                            Bulk Message
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form>
                            <div class="mb-3">
                                <label class="form-label text-light">Message Type</label>
                                <select class="form-select bg-secondary text-light border-secondary">
                                    <option value="sms">SMS</option>
                                    <option value="email">Email</option>
                                    <option value="whatsapp">WhatsApp</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">Target Audience</label>
                                <select class="form-select bg-secondary text-light border-secondary">
                                    <option value="all">All Contacts</option>
                                    <option value="group">Specific Group</option>
                                    <option value="filter">Custom Filter</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">Message Template</label>
                                <select class="form-select bg-secondary text-light border-secondary">
                                    <option value="">Select a template...</option>
                                    <option value="welcome">Welcome Message</option>
                                    <option value="promo">Promotional Message</option>
                                    <option value="custom">Custom Message</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label text-light">Message Content</label>
                                <textarea class="form-control bg-secondary text-light border-secondary" rows="5" placeholder="Type your message or select a template..."></textarea>
                            </div>
                            <div class="alert alert-info">
                                <strong>Preview:</strong> This message will be sent to approximately <strong>0 contacts</strong>.
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer border-secondary">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-outline-primary">Preview</button>
                        <button type="button" class="btn btn-primary">Send to All</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const existingModal = document.getElementById('bulkMessageModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('bulkMessageModal'));
    modal.show();
    
    setTimeout(() => feather.replace(), 100);
}

window.CoolBlue = {
    showButtonLoading,
    hideButtonLoading,
    copyToClipboard,
    showNotification,
    confirmDelete,
    TemplateUtils,
    showSendMessageModal,
    showBulkMessageModal
};
