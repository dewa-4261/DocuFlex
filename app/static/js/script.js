document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const dragDropArea = document.getElementById('dragDropArea');
    const fileInput = document.getElementById('fileInput');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const fileType = document.getElementById('fileType');
    const clearFileBtn = document.getElementById('clearFile');
    const pdfToolsBtn = document.getElementById('pdfToolsBtn');
    const imageToolsBtn = document.getElementById('imageToolsBtn');
    const documentToolsBtn = document.getElementById('documentToolsBtn');
    const pdfToolsPanel = document.getElementById('pdfToolsPanel');
    const imageToolsPanel = document.getElementById('imageToolsPanel');
    const documentToolsPanel = document.getElementById('documentToolsPanel');
    const processingOverlay = document.getElementById('processingOverlay');
    
    // Ensure the processing overlay is hidden on page load
    if (processingOverlay) {
        processingOverlay.style.display = 'none';
    }
    
    // Add animated entrance to main elements
    animateEntranceSequentially();
    
    // PDF Tool cards
    const mergePdf = document.getElementById('mergePdf');
    const splitPdf = document.getElementById('splitPdf');
    const pdfToImages = document.getElementById('pdfToImages');
    const compressPdf = document.getElementById('compressPdf');
    const addPdfWatermark = document.getElementById('addPdfWatermark');
    const wordToPdf = document.getElementById('wordToPdf');
    const excelToPdf = document.getElementById('excelToPdf');
    const imagesToPdf = document.getElementById('imagesToPdf');
    const unlockPdf = document.getElementById('unlockPdf');
    const lockPdf = document.getElementById('lockPdf');
    
    // Image Tool cards
    const imageToPdf = document.getElementById('imageToPdf');
    const removeBackground = document.getElementById('removeBackground');
    const compressImage = document.getElementById('compressImage');
    const addImageWatermark = document.getElementById('addImageWatermark');
    const resizeImage = document.getElementById('resizeImage');
    const cropImage = document.getElementById('cropImage');
    const convertToJpg = document.getElementById('convertToJpg');
    const convertFromJpg = document.getElementById('convertFromJpg');
    
    // PDF Forms
    const mergePdfForm = document.getElementById('mergePdfForm');
    const splitPdfForm = document.getElementById('splitPdfForm');
    const pdfToImagesForm = document.getElementById('pdfToImagesForm');
    const compressPdfForm = document.getElementById('compressPdfForm');
    const addPdfWatermarkForm = document.getElementById('addPdfWatermarkForm');
    const wordToPdfForm = document.getElementById('wordToPdfForm');
    const excelToPdfForm = document.getElementById('excelToPdfForm');
    const imagesToPdfForm = document.getElementById('imagesToPdfForm');
    const unlockPdfForm = document.getElementById('unlockPdfForm');
    const lockPdfForm = document.getElementById('lockPdfForm');
    
    // Image Forms
    const imageToPdfForm = document.getElementById('imageToPdfForm');
    const removeBackgroundForm = document.getElementById('removeBackgroundForm');
    const compressImageForm = document.getElementById('compressImageForm');
    const addImageWatermarkForm = document.getElementById('addImageWatermarkForm');
    const resizeImageForm = document.getElementById('resizeImageForm');
    const cropImageForm = document.getElementById('cropImageForm');
    const convertToJpgForm = document.getElementById('convertToJpgForm');
    const convertFromJpgForm = document.getElementById('convertFromJpgForm');
    
    // Range inputs
    const opacityRange = document.getElementById('opacity');
    const opacityValue = document.getElementById('opacityValue');
    const imageQualityRange = document.getElementById('imageQuality');
    const imageQualityValue = document.getElementById('imageQualityValue');
    const imageOpacityRange = document.getElementById('imageOpacity');
    const imageOpacityValue = document.getElementById('imageOpacityValue');
    const resizePercentage = document.getElementById('resizePercentage');
    const percentageValue = document.getElementById('percentageValue');
    const jpgQualityRange = document.getElementById('jpgQuality');
    const jpgQualityValue = document.getElementById('jpgQualityValue');
    
    // Add animations to tool cards
    animateToolCards();
    
    // File upload handling
    fileInput.addEventListener('change', function(e) {
        handleFileSelection(e.target.files[0]);
    });
    
    dragDropArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        dragDropArea.classList.add('dragover');
    });
    
    dragDropArea.addEventListener('dragleave', function() {
        dragDropArea.classList.remove('dragover');
    });
    
    dragDropArea.addEventListener('drop', function(e) {
        e.preventDefault();
        dragDropArea.classList.remove('dragover');
        
        if (e.dataTransfer.files.length) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });
    
    dragDropArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    clearFileBtn.addEventListener('click', function() {
        clearFilePreview();
    });
    
    // Tool selection
    pdfToolsBtn.addEventListener('click', function() {
        hideAllPanels();
        showPanelWithAnimation(pdfToolsPanel);
    });
    
    imageToolsBtn.addEventListener('click', function() {
        hideAllPanels();
        showPanelWithAnimation(imageToolsPanel);
    });
    
    documentToolsBtn.addEventListener('click', function() {
        hideAllPanels();
        showPanelWithAnimation(documentToolsPanel);
    });
    
    // PDF Tool cards event listeners
    if (mergePdf) mergePdf.addEventListener('click', function() { showToolForm(mergePdfForm); });
    if (splitPdf) splitPdf.addEventListener('click', function() { showToolForm(splitPdfForm); });
    if (pdfToImages) pdfToImages.addEventListener('click', function() { showToolForm(pdfToImagesForm); });
    if (compressPdf) compressPdf.addEventListener('click', function() { showToolForm(compressPdfForm); });
    if (addPdfWatermark) addPdfWatermark.addEventListener('click', function() { showToolForm(addPdfWatermarkForm); });
    if (wordToPdf) wordToPdf.addEventListener('click', function() { showToolForm(wordToPdfForm); });
    if (excelToPdf) excelToPdf.addEventListener('click', function() { showToolForm(excelToPdfForm); });
    if (imagesToPdf) imagesToPdf.addEventListener('click', function() { showToolForm(imagesToPdfForm); });
    if (unlockPdf) unlockPdf.addEventListener('click', function() { showToolForm(unlockPdfForm); });
    if (lockPdf) lockPdf.addEventListener('click', function() { showToolForm(lockPdfForm); });
    
    // Image Tool cards event listeners
    if (imageToPdf) imageToPdf.addEventListener('click', function() { showToolForm(imageToPdfForm); });
    if (removeBackground) removeBackground.addEventListener('click', function() { showToolForm(removeBackgroundForm); });
    if (compressImage) compressImage.addEventListener('click', function() { showToolForm(compressImageForm); });
    if (addImageWatermark) addImageWatermark.addEventListener('click', function() { showToolForm(addImageWatermarkForm); });
    if (resizeImage) resizeImage.addEventListener('click', function() { showToolForm(resizeImageForm); });
    if (cropImage) cropImage.addEventListener('click', function() { showToolForm(cropImageForm); });
    if (convertToJpg) convertToJpg.addEventListener('click', function() { showToolForm(convertToJpgForm); });
    if (convertFromJpg) convertFromJpg.addEventListener('click', function() { showToolForm(convertFromJpgForm); });
    
    // Batch processing
    const batchImageProcessing = document.getElementById('batchImageProcessing');
    const batchImageProcessingForm = document.getElementById('batchImageProcessingForm');
    
    if (batchImageProcessing) batchImageProcessing.addEventListener('click', function() { showToolForm(batchImageProcessingForm); });
    
    // Batch processing form options
    const batchProcessType = document.getElementById('batchProcessType');
    const batchCompressOptions = document.getElementById('batchCompressOptions');
    const batchResizeOptions = document.getElementById('batchResizeOptions');
    const batchQuality = document.getElementById('batchQuality');
    const batchQualityValue = document.getElementById('batchQualityValue');
    const batchResizePercentage = document.getElementById('batchResizePercentage');
    const batchResizePercentageValue = document.getElementById('batchResizePercentageValue');
    
    if (batchProcessType) {
        batchProcessType.addEventListener('change', function() {
            if (batchProcessType.value === 'compress') {
                batchCompressOptions.hidden = false;
                batchResizeOptions.hidden = true;
            } else if (batchProcessType.value === 'resize') {
                batchCompressOptions.hidden = true;
                batchResizeOptions.hidden = false;
            } else {
                batchCompressOptions.hidden = true;
                batchResizeOptions.hidden = true;
            }
        });
    }
    
    if (batchQuality && batchQualityValue) {
        batchQuality.addEventListener('input', function() {
            batchQualityValue.textContent = `${batchQuality.value}%`;
        });
    }
    
    if (batchResizePercentage && batchResizePercentageValue) {
        batchResizePercentage.addEventListener('input', function() {
            batchResizePercentageValue.textContent = `${batchResizePercentage.value}%`;
        });
    }
    
    // Range sliders
    if (opacityRange && opacityValue) {
        opacityRange.addEventListener('input', function() {
            opacityValue.textContent = `${Math.round(opacityRange.value * 100)}%`;
        });
    }
    
    if (imageQualityRange && imageQualityValue) {
        imageQualityRange.addEventListener('input', function() {
            imageQualityValue.textContent = `${imageQualityRange.value}%`;
        });
    }
    
    if (imageOpacityRange && imageOpacityValue) {
        imageOpacityRange.addEventListener('input', function() {
            imageOpacityValue.textContent = `${Math.round(imageOpacityRange.value * 100)}%`;
        });
    }
    
    if (resizePercentage && percentageValue) {
        resizePercentage.addEventListener('input', function() {
            percentageValue.textContent = `${resizePercentage.value}%`;
        });
    }
    
    if (jpgQualityRange && jpgQualityValue) {
        jpgQualityRange.addEventListener('input', function() {
            jpgQualityValue.textContent = `${jpgQualityRange.value}%`;
        });
    }
    
    // Resize image form toggle
    if (document.getElementById('resizeType')) {
        document.getElementById('resizeType').addEventListener('change', toggleResizeFields);
    }
    
    // Handle form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            showProcessingOverlay();
        });
    });
    
    // Handle image crop upload
    const imageToCrop = document.getElementById('imageToCrop');
    let cropper;
    
    if (imageToCrop) {
        imageToCrop.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const cropContainer = document.getElementById('cropContainer');
                    const previewImage = document.getElementById('cropPreviewImage');
                    
                    previewImage.src = e.target.result;
                    cropContainer.hidden = false;
                    
                    // Destroy existing cropper if it exists
                    if (cropper) {
                        cropper.destroy();
                    }
                    
                    // Initialize Cropper.js
                    cropper = new Cropper(previewImage, {
                        aspectRatio: NaN,
                        viewMode: 1,
                        dragMode: 'move',
                        crop: function(event) {
                            document.getElementById('cropX').value = Math.round(event.detail.x);
                            document.getElementById('cropY').value = Math.round(event.detail.y);
                            document.getElementById('cropWidth').value = Math.round(event.detail.width);
                            document.getElementById('cropHeight').value = Math.round(event.detail.height);
                        }
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Document Tool cards
    const shareDocument = document.getElementById('shareDocument');
    const protectedShareDocument = document.getElementById('protectedShareDocument');
    const ocrDocument = document.getElementById('ocrDocument');
    
    // Document Forms
    const shareDocumentForm = document.getElementById('shareDocumentForm');
    const protectedShareDocumentForm = document.getElementById('protectedShareDocumentForm');
    const ocrDocumentForm = document.getElementById('ocrDocumentForm');
    
    // Document Tool cards event listeners
    if (shareDocument) shareDocument.addEventListener('click', function() { showToolForm(shareDocumentForm); });
    if (protectedShareDocument) protectedShareDocument.addEventListener('click', function() { showToolForm(protectedShareDocumentForm); });
    if (ocrDocument) ocrDocument.addEventListener('click', function() { showToolForm(ocrDocumentForm); });
    
    // Helper functions
    function handleFileSelection(file) {
        if (!file) return;
        
        // Hide drag area with animation
        fadeOut(dragDropArea, function() {
            dragDropArea.hidden = true;
            
            // Show file preview with animation
            filePreview.hidden = false;
            fadeIn(filePreview);
            
            fileName.textContent = file.name;
            
            // Determine file type
            const fileExtension = file.name.split('.').pop().toLowerCase();
            
            if (['pdf'].includes(fileExtension)) {
                fileType.textContent = 'PDF Document';
                filePreview.querySelector('.file-icon').className = 'fas fa-file-pdf file-icon';
                
                // Show PDF tools
                hideAllPanels();
                showPanelWithAnimation(pdfToolsPanel);
            } else if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'].includes(fileExtension)) {
                fileType.textContent = 'Image File';
                filePreview.querySelector('.file-icon').className = 'fas fa-file-image file-icon';
                
                // Show Image tools
                hideAllPanels();
                showPanelWithAnimation(imageToolsPanel);
            } else if (['doc', 'docx'].includes(fileExtension)) {
                fileType.textContent = 'Word Document';
                filePreview.querySelector('.file-icon').className = 'fas fa-file-word file-icon';
                
                // Show PDF tools (for Word to PDF conversion)
                hideAllPanels();
                showPanelWithAnimation(pdfToolsPanel);
            } else if (['xls', 'xlsx'].includes(fileExtension)) {
                fileType.textContent = 'Excel Spreadsheet';
                filePreview.querySelector('.file-icon').className = 'fas fa-file-excel file-icon';
                
                // Show PDF tools (for Excel to PDF conversion)
                hideAllPanels();
                showPanelWithAnimation(pdfToolsPanel);
            } else {
                fileType.textContent = 'Unsupported File';
                filePreview.querySelector('.file-icon').className = 'fas fa-file file-icon';
            }
        });
    }
    
    function clearFilePreview() {
        fadeOut(filePreview, function() {
            filePreview.hidden = true;
            dragDropArea.hidden = false;
            fadeIn(dragDropArea);
            fileInput.value = '';
        });
    }
    
    function hideAllPanels() {
        if (!pdfToolsPanel.hidden) fadeOut(pdfToolsPanel, function() { pdfToolsPanel.hidden = true; });
        if (!imageToolsPanel.hidden) fadeOut(imageToolsPanel, function() { imageToolsPanel.hidden = true; });
        if (!documentToolsPanel.hidden) fadeOut(documentToolsPanel, function() { documentToolsPanel.hidden = true; });
        hideAllForms();
    }
    
    function hideAllForms() {
        const forms = document.querySelectorAll('.tool-form');
        forms.forEach(form => {
            if (!form.hidden) {
                fadeOut(form, function() { form.hidden = true; });
            }
        });
    }
    
    function showToolForm(form) {
        hideAllForms();
        form.hidden = false;
        fadeIn(form);
        
        // Scroll to the form with smooth animation
        form.scrollIntoView({ behavior: 'smooth' });
    }
    
    function toggleResizeFields() {
        const resizeType = document.getElementById('resizeType');
        const percentageField = document.getElementById('percentageField');
        const dimensionsFields = document.querySelectorAll('.dimensions-fields');
        
        if (resizeType.value === 'percentage') {
            percentageField.hidden = false;
            fadeIn(percentageField);
            dimensionsFields.forEach(field => {
                fadeOut(field, function() { field.hidden = true; });
            });
        } else {
            fadeOut(percentageField, function() { percentageField.hidden = true; });
            dimensionsFields.forEach(field => {
                field.hidden = false;
                fadeIn(field);
            });
        }
    }
    
    // Animation Helper Functions
    function fadeIn(element, callback) {
        element.style.opacity = 0;
        element.style.display = element.tagName === 'SECTION' ? 'block' : '';
        
        let opacity = 0;
        const timer = setInterval(function() {
            opacity += 0.1;
            element.style.opacity = opacity;
            
            if (opacity >= 1) {
                clearInterval(timer);
                element.style.opacity = '';
                if (callback) callback();
            }
        }, 20);
    }
    
    function fadeOut(element, callback) {
        let opacity = 1;
        const timer = setInterval(function() {
            opacity -= 0.1;
            element.style.opacity = opacity;
            
            if (opacity <= 0) {
                clearInterval(timer);
                element.style.opacity = '';
                if (callback) callback();
            }
        }, 20);
    }
    
    function showPanelWithAnimation(panel) {
        panel.hidden = false;
        panel.style.opacity = 0;
        panel.style.transform = 'translateY(20px)';
        
        setTimeout(function() {
            panel.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            panel.style.opacity = 1;
            panel.style.transform = 'translateY(0)';
            
            setTimeout(function() {
                panel.style.transition = '';
                panel.style.opacity = '';
                panel.style.transform = '';
                
                // Animate tool cards
                const toolCards = panel.querySelectorAll('.tool-card');
                animateElementsSequentially(toolCards, 50);
            }, 300);
        }, 10);
    }
    
    function animateEntranceSequentially() {
        // Set initial state for header
        const header = document.querySelector('header');
        if (header) {
            header.style.opacity = 0;
            setTimeout(() => {
                header.style.transition = 'opacity 0.5s ease';
                header.style.opacity = 1;
            }, 100);
        }
        
        // Animate drag drop area
        setTimeout(() => {
            if (dragDropArea) {
                dragDropArea.style.opacity = 0;
                dragDropArea.style.transform = 'scale(0.95)';
                dragDropArea.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                dragDropArea.style.opacity = 1;
                dragDropArea.style.transform = 'scale(1)';
            }
        }, 300);
        
        // Animate tool selection
        const toolSelection = document.querySelector('.manual-tool-selection');
        if (toolSelection) {
            toolSelection.style.opacity = 0;
            setTimeout(() => {
                toolSelection.style.transition = 'opacity 0.5s ease';
                toolSelection.style.opacity = 1;
                
                // Animate buttons
                const buttons = toolSelection.querySelectorAll('.tool-btn');
                animateElementsSequentially(buttons, 100);
            }, 600);
        }
    }
    
    function animateElementsSequentially(elements, delay) {
        elements.forEach((element, index) => {
            element.style.opacity = 0;
            element.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                element.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                element.style.opacity = 1;
                element.style.transform = 'translateY(0)';
                
                setTimeout(() => {
                    element.style.transition = '';
                }, 300);
            }, index * delay);
        });
    }
    
    function animateToolCards() {
        // Add animation to tool cards when they become visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        document.querySelectorAll('.tool-card').forEach(card => {
            observer.observe(card);
        });
    }
    
    function showProcessingOverlay() {
        if (processingOverlay) {
            processingOverlay.style.display = 'flex';
            processingOverlay.style.opacity = 0;
            
            setTimeout(function() {
                processingOverlay.style.transition = 'opacity 0.3s ease';
                processingOverlay.style.opacity = 1;
            }, 10);
        }
    }
});

// Global function to hide tool forms
function hideToolForm(formId) {
    const form = document.getElementById(formId);
    
    // Fade out animation
    form.style.opacity = 1;
    form.style.transition = 'opacity 0.3s ease';
    form.style.opacity = 0;
    
    setTimeout(function() {
        form.hidden = true;
        form.style.opacity = '';
        form.style.transition = '';
    }, 300);
} 