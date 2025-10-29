document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations for elements with animation classes
    const animatedElements = document.querySelectorAll('.fade-in, .slide-up');
    
    // Create an intersection observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    // Observe all animated elements
    animatedElements.forEach(el => {
        observer.observe(el);
    });
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const requiredInputs = form.querySelectorAll('[required]');
        const submitBtn = form.querySelector('button[type="submit"]');
        
        if (requiredInputs.length > 0 && submitBtn) {
            // Initial check
            checkFormValidity();
            
            // Check on input change
            requiredInputs.forEach(input => {
                input.addEventListener('input', checkFormValidity);
            });
            
            function checkFormValidity() {
                let isValid = true;
                
                requiredInputs.forEach(input => {
                    if (!input.value.trim()) {
                        isValid = false;
                    }
                });
                
                submitBtn.disabled = !isValid;
            }
        }
    });
    
    // File upload handling
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileNameDisplay = document.getElementById('file-name');
            if (fileNameDisplay) {
                if (this.files.length > 0) {
                    fileNameDisplay.textContent = this.files[0].name;
                    fileNameDisplay.classList.add('file-selected');
                    
                    // Enable submit button if it was disabled
                    const submitBtn = this.closest('form').querySelector('button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.disabled = false;
                    }
                } else {
                    fileNameDisplay.textContent = '';
                    fileNameDisplay.classList.remove('file-selected');
                }
            }
        });
    });
    
    // Drag and drop functionality
    const dropAreas = document.querySelectorAll('.upload-area');
    dropAreas.forEach(area => {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            area.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        ['dragenter', 'dragover'].forEach(eventName => {
            area.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            area.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            area.classList.add('highlight');
        }
        
        function unhighlight() {
            area.classList.remove('highlight');
        }
        
        area.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                // Find the file input within the same form or container
                const fileInput = area.querySelector('input[type="file"]') || 
                                  document.querySelector('input[type="file"]');
                
                if (fileInput) {
                    // Update the file input with the dropped file
                    fileInput.files = files;
                    
                    // Trigger the change event to update UI
                    const changeEvent = new Event('change', { bubbles: true });
                    fileInput.dispatchEvent(changeEvent);
                }
            }
        }
    });
});