
// ── Auth Guard ─────────────────────────────────
// Redirect to login if no token found
const token = localStorage.getItem('access_token');
const username = localStorage.getItem('username') || 'User';

if (!token) {
    window.location.href = '/login';
} else {
    const appEl = document.getElementById('app');
    if (appEl) {
        appEl.style.display = 'flex';
    }
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

    // If token expired, redirect to login
    if (response.status === 401) {
        localStorage.clear();
        window.location.href = 'login.html';
        return null;
    }

    return response;
}

// ── Load Documents in Sidebar ──────────────────
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
            <div class="doc-item" title="${doc.title}">
                <span class="doc-item-icon">📄</span>
                <div>
                    <div class="doc-item-name">${doc.title}</div>
                    <div class="doc-item-size">
                        ${formatFileSize(doc.file_size)} ·
                        ${doc.is_processed ? '✅ Ready' : '⏳ Processing'}
                    </div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

// ── Load Chat History in Sidebar ───────────────
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

// ── Helper: Load Question from History ─────────
function loadHistoryQuestion(question) {
    document.getElementById('questionInput').value = question;
    document.getElementById('questionInput').focus();
}

// ── Sidebar Toggle (Mobile) ────────────────────
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// ── Logout ─────────────────────────────────────
function handleLogout() {
    localStorage.clear();
    window.location.href = 'login.html';
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
    document.getElementById('fileSize').textContent =
        formatFileSize(file.size);
    document.getElementById('fileInfo').style.display = 'flex';
    document.getElementById('titleGroup').style.display = 'block';
}

function removeFile() {
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('titleGroup').style.display = 'none';
}

// ── Format File Size ───────────────────────────
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// ── Escape HTML ────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// ── Textarea Auto Resize ───────────────────────
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
}

// ── Enter Key Handler ──────────────────────────
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendQuestion();
    }
}

// ── Initialize App ─────────────────────────────
loadDocuments();
loadHistory();