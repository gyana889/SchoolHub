document.addEventListener('DOMContentLoaded', () => {
    if (window.lucide) window.lucide.createIcons();
    const themeButtons = document.querySelectorAll('[data-theme-choice]');
    const setTheme = (theme) => {
        document.documentElement.dataset.theme = theme;
        themeButtons.forEach((button) => {
            button.setAttribute('aria-pressed', String(button.dataset.themeChoice === theme));
        });
    };
    setTheme(document.documentElement.dataset.theme || 'sage');
    themeButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const theme = button.dataset.themeChoice;
            setTheme(theme);
            try { localStorage.setItem('schoolhub-theme', theme); } catch (error) {}
        });
    });
    const menu = document.querySelector('.mobile-menu');
    const sidebar = document.querySelector('.sidebar');
    if (menu && sidebar) {
        menu.addEventListener('click', () => {
            const open = sidebar.classList.toggle('is-open');
            menu.setAttribute('aria-expanded', String(open));
        });
        sidebar.querySelector('.sidebar-close')?.addEventListener('click', () => {
            sidebar.classList.remove('is-open');
            menu.setAttribute('aria-expanded', 'false');
            menu.focus();
        });
    }
    const sideMenus = document.querySelectorAll('.side-menu');
    sideMenus.forEach((sideMenu) => {
        sideMenu.addEventListener('toggle', () => {
            if (sideMenu.open) {
                sideMenus.forEach((otherMenu) => {
                    if (otherMenu !== sideMenu) otherMenu.open = false;
                });
            }
        });
    });
    const toggle = document.querySelector('.password-toggle');
    const password = document.querySelector('#id_password');
    if (toggle && password) {
        toggle.addEventListener('click', () => {
            const visible = password.type === 'password';
            password.type = visible ? 'text' : 'password';
            toggle.setAttribute('aria-label', visible ? 'Hide password' : 'Show password');
            toggle.setAttribute('title', visible ? 'Hide password' : 'Show password');
        });
    }
});