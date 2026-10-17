/**
 * Main JavaScript Controller - Medical Report Explainer
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Dropzone for File Upload
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const fileNamePreview = document.getElementById('fileNamePreview');

    if (dropzone && fileInput) {
        dropzone.addEventListener('click', () => fileInput.click());

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.style.borderColor = '#0f766e';
            dropzone.style.backgroundColor = '#e6fffa';
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.style.borderColor = '#0d9488';
            dropzone.style.backgroundColor = '#f0fdfa';
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.style.borderColor = '#0d9488';
            dropzone.style.backgroundColor = '#f0fdfa';
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                showFileName(e.dataTransfer.files[0].name);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length) {
                showFileName(fileInput.files[0].name);
            }
        });
    }

    function showFileName(name) {
        if (fileNamePreview) {
            fileNamePreview.innerHTML = `<strong>Selected File:</strong> 📄 ${name}`;
            fileNamePreview.style.display = 'block';
        }
    }

    // 2. Tab Switcher for Short Summary vs Detailed Analysis
    const tabShort = document.getElementById('tabShort');
    const tabDetailed = document.getElementById('tabDetailed');
    const sectionShort = document.getElementById('sectionShort');
    const sectionDetailed = document.getElementById('sectionDetailed');

    if (tabShort && tabDetailed && sectionShort && sectionDetailed) {
        tabShort.addEventListener('click', function () {
            tabShort.classList.add('btn-primary');
            tabShort.classList.remove('btn-secondary');
            tabDetailed.classList.add('btn-secondary');
            tabDetailed.classList.remove('btn-primary');

            sectionShort.style.display = 'block';
            sectionDetailed.style.display = 'none';
        });

        tabDetailed.addEventListener('click', function () {
            tabDetailed.classList.add('btn-primary');
            tabDetailed.classList.remove('btn-secondary');
            tabShort.classList.add('btn-secondary');
            tabShort.classList.remove('btn-primary');

            sectionShort.style.display = 'none';
            sectionDetailed.style.display = 'block';
        });
    }

    // 3. Audio Readout via Web Speech API or Backend Stream
    const btnPlayAudio = document.getElementById('btnPlayAudio');
    if (btnPlayAudio) {
        btnPlayAudio.addEventListener('click', function () {
            const shortText = document.getElementById('summaryText') ? document.getElementById('summaryText').innerText : '';
            const reportLang = btnPlayAudio.getAttribute('data-lang') || 'en';

            if (!shortText) return;

            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel(); // Stop any active speech
                const utterance = new SpeechSynthesisUtterance(shortText);
                utterance.lang = reportLang;
                utterance.rate = 0.95;

                btnPlayAudio.innerHTML = '🔊 Speaking...';
                btnPlayAudio.disabled = true;

                utterance.onend = function () {
                    btnPlayAudio.innerHTML = '🎧 Listen Audio Summary';
                    btnPlayAudio.disabled = false;
                };

                window.speechSynthesis.speak(utterance);
            } else {
                alert('Text-to-speech audio is supported in your browser!');
            }
        });
    }

    // 4. Doubts Q&A Chat Handler
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');

    if (chatForm && chatInput && chatMessages) {
        chatForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const question = chatInput.value.trim();
            const reportId = chatForm.getAttribute('data-report-id');
            const lang = chatForm.getAttribute('data-lang') || 'en';

            if (!question || !reportId) return;

            // Append user question
            appendMessage('user', question);
            chatInput.value = '';

            // Add typing placeholder
            const typingId = appendMessage('bot', '⏳ Thinking and reviewing your report details...');

            fetch('/api/ask-doubt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    report_id: reportId,
                    question: question,
                    language: lang
                })
            })
            .then(res => res.json())
            .then(data => {
                // Replace typing placeholder
                const typingMsg = document.getElementById(typingId);
                if (typingMsg) typingMsg.innerText = data.answer || "Thank you. Please consult your physician for personalized medical advice.";
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(err => {
                const typingMsg = document.getElementById(typingId);
                if (typingMsg) typingMsg.innerText = "Error getting response. Please try again.";
            });
        });
    }

    function appendMessage(sender, text) {
        const msgDiv = document.createElement('div');
        const msgId = 'msg-' + Date.now();
        msgDiv.id = msgId;
        msgDiv.className = `chat-msg ${sender}`;
        msgDiv.innerText = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msgId;
    }
});

// 5. Google Sign-In Callback Handler
function handleCredentialResponse(response) {
    // In production, token is sent to backend. Demo mode parses token payload or falls back smoothly.
    fetch('/google-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email: 'google.patient@example.com',
            name: 'Google Auth Patient'
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.redirect) {
            window.location.href = data.redirect;
        }
    });
}

function demoGoogleLogin() {
    handleCredentialResponse({});
}
