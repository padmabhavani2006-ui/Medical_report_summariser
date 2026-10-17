/**
 * app.js - Client-Side Interactive Engine for MEDExplain AI
 * Handles Drag & Drop upload, file previewing, text character counter,
 * form submission, calm progress overlay, and popover interactions.
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // -------------------------------------------------------------------------
    // 1. User Profile Popover Menu
    // -------------------------------------------------------------------------
    const userMenuToggle = document.getElementById('userMenuToggle');
    const userPopover = document.getElementById('userPopover');

    if (userMenuToggle && userPopover) {
        userMenuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            userPopover.classList.toggle('active');
        });

        document.addEventListener('click', function(e) {
            if (!userPopover.contains(e.target) && !userMenuToggle.contains(e.target)) {
                userPopover.classList.remove('active');
            }
        });
    }

    // -------------------------------------------------------------------------
    // 2. Upload Mode Tabs Switcher (File vs Text)
    // -------------------------------------------------------------------------
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabFileContent = document.getElementById('tabFileContent');
    const tabTextContent = document.getElementById('tabTextContent');
    const inputModeHidden = document.getElementById('inputMode');

    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const targetTab = this.getAttribute('data-tab');
                
                tabBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                if (targetTab === 'file') {
                    if (tabFileContent) tabFileContent.classList.add('active');
                    if (tabTextContent) tabTextContent.classList.remove('active');
                    if (inputModeHidden) inputModeHidden.value = 'file';
                } else {
                    if (tabFileContent) tabFileContent.classList.remove('active');
                    if (tabTextContent) tabTextContent.classList.add('active');
                    if (inputModeHidden) inputModeHidden.value = 'text';
                }
            });
        });
    }

    // -------------------------------------------------------------------------
    // 3. Drag & Drop and File Selection Preview
    // -------------------------------------------------------------------------
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const btnBrowseFiles = document.getElementById('btnBrowseFiles');
    const dropIdle = document.getElementById('dropIdle');
    const filePreview = document.getElementById('filePreview');
    const previewMedia = document.getElementById('previewMedia');
    const previewFileName = document.getElementById('previewFileName');
    const previewFileDetails = document.getElementById('previewFileDetails');
    const btnRemoveFile = document.getElementById('btnRemoveFile');

    if (dropZone && fileInput) {
        // Trigger file input click when browsing
        if (btnBrowseFiles) {
            btnBrowseFiles.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.click();
            });
        }

        dropZone.addEventListener('click', () => {
            if (!fileInput.files || fileInput.files.length === 0) {
                fileInput.click();
            }
        });

        // Dragover events
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('dragover');
            });
        });

        // Handle File Drop
        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files.length > 0) {
                fileInput.files = dt.files;
                handleFileSelection(dt.files[0]);
            }
        });

        // Handle File Input Change
        fileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                handleFileSelection(this.files[0]);
            }
        });

        // Remove selected file
        if (btnRemoveFile) {
            btnRemoveFile.addEventListener('click', (e) => {
                e.stopPropagation();
                resetFileSelection();
            });
        }
    }

    function handleFileSelection(file) {
        if (!file) return;

        const allowedExts = ['pdf', 'jpg', 'jpeg', 'png', 'webp'];
        const ext = file.name.split('.').pop().toLowerCase();

        if (!allowedExts.includes(ext)) {
            showErrorAlert('Unsupported file type. Please upload a PDF (.pdf) or medical report image (.jpg, .png, .webp).');
            resetFileSelection();
            return;
        }

        if (file.size > 16 * 1024 * 1024) {
            showErrorAlert('File size exceeds 16 MB. Please select a smaller medical report file.');
            resetFileSelection();
            return;
        }

        // Render preview UI
        if (previewFileName) previewFileName.textContent = file.name;
        if (previewFileDetails) previewFileDetails.textContent = `${ext.toUpperCase()} File • ${formatFileSize(file.size)}`;

        if (previewMedia) {
            previewMedia.innerHTML = '';
            if (['jpg', 'jpeg', 'png', 'webp'].includes(ext)) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.createElement('img');
                    img.src = e.target.result;
                    previewMedia.appendChild(img);
                };
                reader.readAsDataURL(file);
            } else {
                // PDF Icon
                previewMedia.innerHTML = `
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                    </svg>`;
            }
        }

        if (dropIdle) dropIdle.classList.add('hidden');
        if (filePreview) filePreview.classList.remove('hidden');
    }

    function resetFileSelection() {
        if (fileInput) fileInput.value = '';
        if (dropIdle) dropIdle.classList.remove('hidden');
        if (filePreview) filePreview.classList.add('hidden');
        if (previewMedia) previewMedia.innerHTML = '';
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    // -------------------------------------------------------------------------
    // 4. Text Input Character Counter
    // -------------------------------------------------------------------------
    const textContentInput = document.getElementById('textContentInput');
    const charCount = document.getElementById('charCount');

    if (textContentInput && charCount) {
        textContentInput.addEventListener('input', function() {
            const count = this.value.length;
            charCount.textContent = `${count.toLocaleString()} character${count === 1 ? '' : 's'}`;
        });
    }

    // -------------------------------------------------------------------------
    // 5. Form Submission & Analysis Progress Overlay
    // -------------------------------------------------------------------------
    const analyzeForm = document.getElementById('analyzeForm');
    const btnAnalyze = document.getElementById('btnAnalyze');
    const loadingState = document.getElementById('analysisLoadingState');
    const loadingStatusText = document.getElementById('loadingStatusText');

    if (analyzeForm) {
        analyzeForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const mode = inputModeHidden ? inputModeHidden.value : 'file';
            const selectedFile = fileInput ? fileInput.files[0] : null;
            const textVal = textContentInput ? textContentInput.value.trim() : '';

            if (mode === 'file' && !selectedFile && !textVal) {
                showErrorAlert('Please select a medical report file or switch to paste text.');
                return;
            }

            if (mode === 'text' && !textVal) {
                showErrorAlert('Please paste or type your medical report text before analyzing.');
                return;
            }

            // Start loading state
            setLoadingState(true);

            const formData = new FormData(analyzeForm);

            fetch('/analyze', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json().then(data => ({ status: response.status, body: data })))
            .then(res => {
                if (res.body.success && res.body.redirect_url) {
                    window.location.href = res.body.redirect_url;
                } else {
                    setLoadingState(false);
                    showErrorAlert(res.body.error || 'Something went wrong while analyzing your report. Please try again.');
                }
            })
            .catch(err => {
                setLoadingState(false);
                showErrorAlert('We couldn\'t connect to the analysis service. Please check your connection and try again.');
            });
        });
    }

    // -------------------------------------------------------------------------
    // 6. Synthetic Demo Report Button Handler
    // -------------------------------------------------------------------------
    const btnSyntheticDemo = document.getElementById('btnSyntheticDemo');
    if (btnSyntheticDemo) {
        btnSyntheticDemo.addEventListener('click', function() {
            setLoadingState(true, 'Analyzing Synthetic Demo Report...');

            const langSelect = document.getElementById('languageSelect');
            const selectedLang = langSelect ? langSelect.value : 'en';

            fetch('/analyze-demo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ language: selectedLang })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    setLoadingState(false);
                    showErrorAlert(data.error || 'Failed to analyze demo report.');
                }
            })
            .catch(() => {
                setLoadingState(false);
                showErrorAlert('Failed to run demo report analysis.');
            });
        });
    }

    function setLoadingState(isLoading, customHeading) {
        if (loadingState) {
            if (isLoading) {
                loadingState.classList.remove('hidden');
                if (btnAnalyze) btnAnalyze.disabled = true;

                const messages = [
                    'Reading your report...',
                    'Extracting important lab test values...',
                    'Evaluating reference ranges...',
                    'Preparing a simple doctor-style explanation...'
                ];
                let msgIdx = 0;
                if (loadingStatusText) loadingStatusText.textContent = customHeading || messages[0];

                window.analysisTimer = setInterval(() => {
                    msgIdx = (msgIdx + 1) % messages.length;
                    if (loadingStatusText && !customHeading) {
                        loadingStatusText.textContent = messages[msgIdx];
                    }
                }, 2200);

            } else {
                loadingState.classList.add('hidden');
                if (btnAnalyze) btnAnalyze.disabled = false;
                if (window.analysisTimer) clearInterval(window.analysisTimer);
            }
        }
    }

    function showErrorAlert(msg) {
        const flashContainer = document.querySelector('.flash-container');
        if (flashContainer) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'flash-alert flash-danger';
            alertDiv.innerHTML = `
                <span class="flash-message">${msg}</span>
                <button class="flash-close" onclick="this.parentElement.remove()">&times;</button>
            `;
            flashContainer.appendChild(alertDiv);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            alert(msg);
        }
    }
});
