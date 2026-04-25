/* ═══════════════════════════════════════════════════════
   AskDocs AI — Theme System
   Cycles: dark → light → rose → dark
   Persists via localStorage, no flash on load
═══════════════════════════════════════════════════════ */

// Apply immediately before render (prevents flash)
(function () {
    const saved = localStorage.getItem('askdocs_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
})();

const THEMES = ['dark', 'light', 'rose'];

const THEME_META = {
    dark:  { label: 'Switch to Light',  next: 'light' },
    light: { label: 'Switch to Rose',   next: 'rose'  },
    rose:  { label: 'Switch to Dark',   next: 'dark'  },
};

function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme') || 'dark';
    const idx = THEMES.indexOf(current);
    const next = THEMES[(idx + 1) % THEMES.length];

    // Apply
    html.setAttribute('data-theme', next);
    localStorage.setItem('askdocs_theme', next);

    // Update button tooltip
    updateThemeButton(next);

    console.log(`Theme → ${next}`);
}

function updateThemeButton(theme) {
    const btn = document.querySelector('.theme-toggle');
    if (!btn) return;
    const meta = THEME_META[theme];
    if (meta) btn.title = meta.label;
}

// Set correct tooltip on load
document.addEventListener('DOMContentLoaded', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    updateThemeButton(current);
});
