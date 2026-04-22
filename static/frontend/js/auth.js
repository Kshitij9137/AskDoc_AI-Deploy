const API_BASE = window.location.origin + '/api';

// ── Helper Functions ───────────────────────────

function showError(msg) {
    const el = document.getElementById('errorMsg');
    el.textContent = msg;
    el.classList.add('show');
}

function hideError() {
    const el = document.getElementById('errorMsg');
    el.classList.remove('show');
}

function showSuccess(msg) {
    const el = document.getElementById('successMsg');
    if (el) {
        el.textContent = msg;
        el.classList.add('show');
    }
}

function setLoading(btnId, loading) {
    const btn = document.getElementById(btnId);
    if (loading) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Please wait...';
    } else {
        btn.disabled = false;
        btn.innerHTML = btnId === 'loginBtn' ? 'Login' : 'Create Account';
    }
}

// ── Check if Already Logged In ─────────────────
// If user visits login page but already has token,
// redirect to main app
if (window.location.pathname.includes('login') ||
    window.location.pathname.includes('register')) {
    const token = localStorage.getItem('access_token');
    if (token) {
        window.location.href = '/app';
    }
}

// ── Login Handler ──────────────────────────────
async function handleLogin() {
    hideError();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    // Basic validation
    if (!username || !password) {
        showError('Please enter both username and password.');
        return;
    }

    setLoading('loginBtn', true);

    try {
        const response = await fetch(`${API_BASE}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Save tokens to localStorage
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            localStorage.setItem('username', username);

            // Redirect to main app
            window.location.href = '/app';
        } else {
            showError(data.detail || 'Invalid username or password.');
        }

    } catch (error) {
        showError('Cannot connect to server. Make sure Django is running.');
    } finally {
        setLoading('loginBtn', false);
    }
}

// ── Register Handler ───────────────────────────
async function handleRegister() {
    hideError();

    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    // Validation
    if (!username || !email || !password) {
        showError('Please fill in all fields.');
        return;
    }

    if (password.length < 8) {
        showError('Password must be at least 8 characters.');
        return;
    }

    setLoading('registerBtn', true);

    try {
        const response = await fetch(`${API_BASE}/auth/register/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, role: 'user' })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess('Account created! Redirecting to login...');
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
        } else {
            // Show first error message from API
            const firstError = Object.values(data)[0];
            showError(Array.isArray(firstError) ? firstError[0] : firstError);
        }

    } catch (error) {
        showError('Cannot connect to server. Make sure Django is running.');
    } finally {
        setLoading('registerBtn', false);
    }
}

// ── Enter Key Support ──────────────────────────
document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        const loginBtn = document.getElementById('loginBtn');
        const registerBtn = document.getElementById('registerBtn');
        if (loginBtn) handleLogin();
        if (registerBtn) handleRegister();
    }
});