(() => {
  'use strict';
  const key = 'mdvu-theme';
  const preference = window.matchMedia('(prefers-color-scheme: dark)');
  let chosen;
  try { chosen = localStorage.getItem(key); } catch { /* Storage may be disabled. */ }
  if (chosen !== 'dark' && chosen !== 'light') chosen = null;
  function apply() {
    const theme = chosen || (preference.matches ? 'dark' : 'light');
    document.documentElement.dataset.theme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#0d1624' : '#f7f9fc');
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      const label = document.documentElement.lang === 'ru'
        ? `Переключить на ${theme === 'dark' ? 'светлую' : 'тёмную'} тему`
        : `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`;
      button.setAttribute('aria-label', label);
      button.title = label;
    });
  }
  // Choose before CSS loads so the initial paint uses the right theme.
  document.documentElement.classList.add('js');
  apply();
  preference.addEventListener('change', apply);
  window.addEventListener('storage', event => {
    if (event.key === key || event.key === null) {
      chosen = event.newValue === 'dark' || event.newValue === 'light' ? event.newValue : null;
      apply();
    }
  });
  document.addEventListener('DOMContentLoaded', () => {
    apply();
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.addEventListener('click', () => {
        chosen = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem(key, chosen); } catch { /* Switching still works on this page. */ }
        apply();
      });
    });
  });
})();
