// ── Auth Guard ─────────────────────────────────
const token = localStorage.getItem('access_token');
const username = localStorage.getItem('username') || 'User';

if (!token) {
    window.location.href = '/login';
} else {
    const appEl = document.getElementById('app');
    if (appEl) appEl.style.display = 'flex';

    const userDisplay = document.getElementById('usernameDisplay');
    const userAvatar = document.getElementById('userAvatar');
    if (userDisplay) userDisplay.textContent = username;
    if (userAvatar) userAvatar.textContent = username.charAt(0).toUpperCase();
}

// ── API Helper ─────────────────────────────────
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json'
    };
    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    const response = await fetch(`${API_BASE}${endpoint}`, options);
    if (response.status === 401) {
        localStorage.clear();
        window.location.href = '/login';
        return null;
    }
    return response;
}

// ── Load Documents ─────────────────────────────
async function loadDocuments() {
    try {
        const response = await apiCall('/documents/');
        if (!response) return;

        const data = await response.json();
        const docs = data.results || data;
        const docList = document.getElementById('docList');

        if (!docs || docs.length === 0) {
            docList.innerHTML =
                '<div class="empty-state-small">No documents yet</div>';
            return;
        }

        docList.innerHTML = docs.map(doc => `
    <div class="doc-item" title="${escapeHtml(doc.title)}" id="doc-${doc.id}">
        <span class="doc-item-icon">📄</span>
        <div class="doc-item-info">
            <div class="doc-item-name">${escapeHtml(doc.title)}</div>
            <div class="doc-item-size">
                ${formatFileSize(doc.file_size)} ·
                ${doc.is_processed ? '✅ Ready' : '⏳ Processing'}
            </div>
        </div>
        <button
            class="doc-delete-btn"
            onclick="deleteDocument(${doc.id}, '${escapeHtml(doc.title)}')"
            title="Delete document"
        >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6" stroke="currentColor"
                      stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </button>
    </div>
`).join('');

    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

// ── Load History ───────────────────────────────
async function loadHistory() {
    try {
        const response = await apiCall('/qa/history/?limit=10');
        if (!response) return;

        const data = await response.json();
        const logs = data.results || [];
        const historyList = document.getElementById('historyList');

        if (logs.length === 0) {
            historyList.innerHTML =
                '<div class="empty-state-small">No history yet</div>';
            return;
        }

        historyList.innerHTML = logs.map(log => `
            <div class="history-item"
                 onclick="loadHistoryQuestion('${escapeHtml(log.question)}')"
                 title="${escapeHtml(log.question)}">
                <div class="history-item-text">
                    💬 ${escapeHtml(log.question)}
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function loadHistoryQuestion(question) {
    document.getElementById('questionInput').value = question;
    document.getElementById('questionInput').focus();
}

// ── Send Question ──────────────────────────────
async function sendQuestion() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();

    if (!question) return;

    // Hide welcome screen on first message
    const welcomeScreen = document.getElementById('welcomeScreen');
    if (welcomeScreen) welcomeScreen.style.display = 'none';

    // Clear input
    input.value = '';
    input.style.height = 'auto';

    // Disable send button
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;

    // Show user message
    appendUserMessage(question);

    // Show typing indicator
    const typingId = showTypingIndicator();

    try {
        const response = await apiCall('/qa/ask/', 'POST', { question });

        // Remove typing indicator
        removeTypingIndicator(typingId);

        if (!response) return;

        const data = await response.json();

        if (response.ok) {
            appendAIMessage(data.answer, data.sources);
            // Refresh history sidebar
            loadHistory();
        } else {
            appendErrorMessage(data.error || 'Something went wrong.');
        }

    } catch (error) {
        removeTypingIndicator(typingId);
        appendErrorMessage('Cannot connect to server. Make sure Django is running.');
    } finally {
        sendBtn.disabled = false;
    }
}

// ── Append User Message ────────────────────────
function appendUserMessage(text) {
    const container = document.getElementById('messagesContainer');
    const initial = username.charAt(0).toUpperCase();

    const div = document.createElement('div');
    div.className = 'message user';
    div.innerHTML = `
        <div class="message-avatar">${initial}</div>
        <div class="message-bubble">
            <div class="message-text">${escapeHtml(text)}</div>
            <div class="message-time">${getTime()}</div>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

// ── Append AI Message ──────────────────────────
function appendAIMessage(answer, sources) {
    const container = document.getElementById('messagesContainer');

    // Build sources HTML
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        // Show only top 3 sources in UI
        // (backend still uses all sources for answer quality)
        const topSources = sources.slice(0, 3);

        const sourceItems = topSources.map(s => `
            <div class="source-item">
                📄 <span>${escapeHtml(s.document)}</span>
                — Page ${s.page}
            </div>
        `).join('');

        sourcesHtml = `
            <div class="message-sources">
                <div class="sources-title">📌 Sources</div>
                ${sourceItems}
            </div>
        `;
    }

    const div = document.createElement('div');
    div.className = 'message ai';
    div.innerHTML = `
        <div class="message-avatar">🧠</div>
        <div class="message-bubble">
            <div class="message-text">${escapeHtml(answer)}</div>
            ${sourcesHtml}
            <div class="message-time">${getTime()}</div>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

// ── Append Error Message ───────────────────────
function appendErrorMessage(text) {
    const container = document.getElementById('messagesContainer');
    const div = document.createElement('div');
    div.className = 'message ai error';
    div.innerHTML = `
        <div class="message-avatar">⚠️</div>
        <div class="message-bubble">
            <div class="message-text">${escapeHtml(text)}</div>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

// ── Typing Indicator ───────────────────────────
function showTypingIndicator() {
    const container = document.getElementById('messagesContainer');
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = id;
    div.innerHTML = `
        <div class="message-avatar" style="
            width:36px; height:36px; border-radius:50%;
            background: linear-gradient(135deg, #1e3a5f, #0d2137);
            border: 1px solid #2d4a6f;
            display:flex; align-items:center;
            justify-content:center; font-size:18px;">
            🧠
        </div>
        <div class="typing-bubble">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ── Helpers ────────────────────────────────────
function scrollToBottom() {
    const chatArea = document.getElementById('chatArea');
    chatArea.scrollTop = chatArea.scrollHeight;
}

function getTime() {
    return new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendQuestion();
    }
}

// ── Sidebar & Logout ───────────────────────────
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

function handleLogout() {
    localStorage.clear();
    window.location.href = '/login';
}

// ── Upload Modal ───────────────────────────────
function openUploadModal() {
    document.getElementById('uploadModal').classList.add('show');
    resetUploadModal();
}

function closeUploadModal() {
    document.getElementById('uploadModal').classList.remove('show');
    resetUploadModal();
}

function resetUploadModal() {
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('titleGroup').style.display = 'none';
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('docTitle').value = '';

    const errorEl = document.getElementById('uploadError');
    const successEl = document.getElementById('uploadSuccess');
    errorEl.classList.remove('show');
    successEl.classList.remove('show');

    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.disabled = false;
    uploadBtn.textContent = 'Upload';
}

function triggerFileInput() {
    document.getElementById('fileInput').click();
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Only PDF files are supported.');
        return;
    }

    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
    document.getElementById('fileInfo').style.display = 'flex';
    document.getElementById('titleGroup').style.display = 'block';
}

function removeFile() {
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('titleGroup').style.display = 'none';
}

// ── Upload Document ────────────────────────────
async function uploadDocument() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        const errorEl = document.getElementById('uploadError');
        errorEl.textContent = 'Please select a PDF file first.';
        errorEl.classList.add('show');
        return;
    }

    const title = document.getElementById('docTitle').value.trim() || file.name;
    const uploadBtn = document.getElementById('uploadBtn');

    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Uploading...';

    // Show progress
    document.getElementById('uploadProgress').style.display = 'block';
    setStep(1, 'active');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);

    try {
        setStep(1, 'active');
        await delay(300);

        const response = await fetch(`${API_BASE}/documents/upload/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            },
            body: formData
        });

        setStep(2, 'active');
        await delay(500);
        setStep(3, 'active');
        await delay(500);
        setStep(4, 'active');
        await delay(300);

        const data = await response.json();

        if (response.ok) {
            // Mark all steps done
            [1, 2, 3, 4].forEach(i => setStepDone(i));

            const successEl = document.getElementById('uploadSuccess');
            successEl.textContent = '✅ Document uploaded and processed successfully!';
            successEl.classList.add('show');

            uploadBtn.textContent = 'Done ✓';

            // Refresh documents list in sidebar
            await loadDocuments();

            // Close modal after 2 seconds
            setTimeout(() => closeUploadModal(), 2000);

        } else {
            const errorEl = document.getElementById('uploadError');
            errorEl.textContent = data.error || 'Upload failed. Please try again.';
            errorEl.classList.add('show');
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Try Again';
        }

    } catch (error) {
        const errorEl = document.getElementById('uploadError');
        errorEl.textContent = 'Cannot connect to server. Make sure Django is running.';
        errorEl.classList.add('show');
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Try Again';
    }
}

function setStep(num, status) {
    const step = document.getElementById(`step${num}`);
    if (!step) return;

    step.className = `progress-step ${status}`;
    const icon = step.querySelector('.step-icon');

    if (status === 'done') {
        icon.textContent = '✅';
    } else if (status === 'active') {
        icon.textContent = '⏳';
        // Mark previous steps as done
        for (let i = 1; i < num; i++) {
            setStepDone(i);
        }
    } else {
        icon.textContent = '⬜';
    }
}

function setStepDone(num) {
    const step = document.getElementById(`step${num}`);
    if (!step) return;
    step.className = 'progress-step done';
    const icon = step.querySelector('.step-icon');
    if (icon) icon.textContent = '✅';
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ── Initialize ─────────────────────────────────
loadDocuments();
loadHistory();

// ── Drag & Drop Support ────────────────────────
const dropZone = document.getElementById('dropZone');
if (dropZone) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');

        const file = e.dataTransfer.files[0];
        if (!file) return;

        if (!file.name.toLowerCase().endsWith('.pdf')) {
            alert('Only PDF files are supported.');
            return;
        }

        // Simulate file input selection
        const fileInput = document.getElementById('fileInput');
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;

        // Show file info
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileSize').textContent =
            formatFileSize(file.size);
        document.getElementById('fileInfo').style.display = 'flex';
        document.getElementById('titleGroup').style.display = 'block';
    });
}

// ── Delete Document ────────────────────────────
async function deleteDocument(docId, docTitle) {
    // Ask for confirmation first
    if (!confirm(`Delete "${docTitle}"?\n\nThis will permanently remove the document and all its data.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/documents/${docId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });

        if (response.ok || response.status === 204) {
            // Remove from sidebar immediately
            const el = document.getElementById(`doc-${docId}`);
            if (el) {
                el.style.transition = 'all 0.3s ease';
                el.style.opacity = '0';
                el.style.transform = 'translateX(-10px)';
                setTimeout(() => {
                    el.remove();
                    // Update doc count
                    const remaining = document.querySelectorAll('.doc-item').length;
                    const countEl = document.getElementById('docCount');
                    if (countEl) countEl.textContent = remaining;
                    // Show empty state if no docs left
                    if (remaining === 0) {
                        document.getElementById('docList').innerHTML =
                            '<div class="sidebar-empty"><p>No documents yet</p></div>';
                    }
                }, 300);
            }
            console.log(`Deleted: ${docTitle}`);
        } else {
            alert('Failed to delete document. Please try again.');
        }

    } catch (error) {
        alert('Cannot connect to server.');
    }
}