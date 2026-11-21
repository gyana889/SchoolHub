document.addEventListener('DOMContentLoaded', () => {
    if (window.lucide) window.lucide.createIcons();
    const idleTimer = document.querySelector('[data-idle-timer]');
    const logoutForm = document.querySelector('[data-logout-form]');
    if (idleTimer && logoutForm) {
        const idleTime = idleTimer.querySelector('[data-idle-time]');
        const storageKey = `schoolhub-idle:${idleTimer.dataset.sessionScope}`;
        const duration = Number(idleTimer.dataset.idleSeconds) * 1000;
        let deadline = Date.now() + duration;
        let lastRenewal = Date.now();
        let renewing = false;
        let renewalTimer = null;
        let signingOut = false;
        const shareDeadline = () => {
            try { localStorage.setItem(storageKey, String(deadline)); } catch (error) {}
        };
        const syncDeadline = () => {
            try { deadline = Math.max(deadline, Number(localStorage.getItem(storageKey)) || 0); } catch (error) {}
        };
        const updateTimer = () => {
            syncDeadline();
            const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
            idleTime.textContent = `${String(Math.floor(remaining / 60)).padStart(2, '0')}:${String(remaining % 60).padStart(2, '0')}`;
            if (!remaining && !signingOut) {
                signingOut = true;
                logoutForm.submit();
            }
        };
        shareDeadline();
        updateTimer();
        window.setInterval(updateTimer, 1000);
        window.addEventListener('storage', (event) => {
            if (event.key === storageKey) updateTimer();
        });
        document.addEventListener('visibilitychange', updateTimer);
        const renewSession = async () => {
            if (signingOut || renewing) return;
            const delay = 30000 - (Date.now() - lastRenewal);
            if (delay > 0) {
                if (!renewalTimer) renewalTimer = window.setTimeout(() => {
                    renewalTimer = null;
                    renewSession();
                }, delay);
                return;
            }
            if (Date.now() >= deadline) {
                updateTimer();
                return;
            }
            renewing = true;
            try {
                const response = await fetch(idleTimer.dataset.renewUrl, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': logoutForm.querySelector('[name=csrfmiddlewaretoken]').value },
                    mode: 'same-origin',
                });
                if (response.status === 401) {
                    signingOut = true;
                    logoutForm.submit();
                } else if (response.ok) {
                    const data = await response.json();
                    lastRenewal = Date.now();
                    deadline = lastRenewal + data.expires_in * 1000;
                    shareDeadline();
                    updateTimer();
                }
            } catch (error) {} finally {
                renewing = false;
            }
        };
        ['pointerdown', 'pointermove', 'keydown', 'scroll', 'touchstart'].forEach((event) => {
            document.addEventListener(event, renewSession, { passive: true });
        });
    }
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
    const mappingForm = document.querySelector('[data-mapping-form]');
    if (mappingForm) {
        const updateMappingMode = () => {
            const selectedMode = mappingForm.querySelector('input[name="table_mode"]:checked')?.value;
            mappingForm.querySelectorAll('[data-table-mode]').forEach((container) => {
                const active = container.dataset.tableMode === selectedMode;
                container.hidden = !active;
                container.querySelectorAll('select, input[type="checkbox"]').forEach((input) => { input.disabled = !active; });
            });
        };
        mappingForm.querySelectorAll('input[name="table_mode"]').forEach((input) => input.addEventListener('change', updateMappingMode));
        updateMappingMode();
        const tableFilter = mappingForm.querySelector('[data-table-filter]');
        const tableCount = mappingForm.querySelector('[data-table-count]');
        const tableOptions = mappingForm.querySelectorAll('#id_tables > div');
        const updateTableCount = () => {
            if (tableCount) tableCount.textContent = `${mappingForm.querySelectorAll('input[name="tables"]:checked').length} selected`;
        };
        tableFilter?.addEventListener('input', () => {
            const search = tableFilter.value.trim().toLowerCase();
            tableOptions.forEach((option) => { option.hidden = !option.textContent.toLowerCase().includes(search); });
        });
        mappingForm.querySelectorAll('input[name="tables"]').forEach((input) => input.addEventListener('change', updateTableCount));
        updateTableCount();
        const columnOptions = mappingForm.querySelector('[data-column-options]');
        const columnInput = mappingForm.querySelector('[data-editable-columns]');
        const submitButton = mappingForm.querySelector('button[type="submit"]');
        const selections = JSON.parse(document.getElementById('mapping-column-selections').textContent);
        let currentRequest = 0;
        const updateColumns = async () => {
            const request = ++currentRequest;
            const mode = mappingForm.querySelector('input[name="table_mode"]:checked')?.value;
            const tables = mode === 'multiple'
                ? Array.from(mappingForm.querySelectorAll('input[name="tables"]:checked'), (input) => input.value)
                : [mappingForm.querySelector('select[name="table"]').value].filter(Boolean);
            columnOptions.replaceChildren();
            submitButton.disabled = tables.length > 0;
            if (tables.length) columnOptions.textContent = 'Loading columns...';
            try {
                const results = await Promise.all(tables.map(async (table) => {
                    const url = new URL(mappingForm.dataset.columnsUrl, window.location.href);
                    url.searchParams.set('table', table);
                    const response = await fetch(url);
                    if (!response.ok) throw new Error('Unable to load columns');
                    return (await response.json()).columns;
                }));
                if (request !== currentRequest) return;
                columnOptions.replaceChildren();
                tables.forEach((table, index) => {
                    const columns = results[index];
                    if (!Array.isArray(selections[table])) selections[table] = selections[table] === null ? columns.slice() : [];
                    const fieldset = document.createElement('fieldset');
                    fieldset.className = 'mapping-mode mapping-columns';
                    const legend = document.createElement('legend');
                    legend.textContent = `Editable columns: ${table}`;
                    fieldset.append(legend);
                    columns.forEach((column) => {
                        const label = document.createElement('label');
                        const checkbox = document.createElement('input');
                        checkbox.type = 'checkbox';
                        checkbox.checked = selections[table].includes(column);
                        checkbox.addEventListener('change', () => {
                            selections[table] = Array.from(fieldset.querySelectorAll('input:checked'), (input) => input.value);
                            syncSelections();
                        });
                        checkbox.value = column;
                        label.append(checkbox, document.createTextNode(` ${column}`));
                        fieldset.append(label);
                    });
                    columnOptions.append(fieldset);
                });
                const syncSelections = () => {
                    columnInput.value = JSON.stringify(Object.fromEntries(tables.map((table) => [table, selections[table]])));
                };
                syncSelections();
                submitButton.disabled = false;
            } catch (error) {
                if (request !== currentRequest) return;
                columnOptions.textContent = 'Could not load columns. Change the table selection to try again.';
            }
        };
        mappingForm.querySelectorAll('input[name="table_mode"], input[name="tables"], select[name="table"]').forEach((input) => input.addEventListener('change', updateColumns));
        updateColumns();
    }
    const recordForm = document.querySelector('[data-dynamic-record-form]');
    if (recordForm) {
        const typeToggleLabel = document.createElement('label');
        typeToggleLabel.className = 'element-type-toggle record-type-toggle';
        typeToggleLabel.hidden = true;
        const typeToggle = document.createElement('input');
        typeToggle.type = 'checkbox';
        typeToggle.setAttribute('aria-label', 'Show input type options');
        const typeToggleTrack = document.createElement('span');
        typeToggleTrack.className = 'element-type-toggle-track';
        typeToggleTrack.setAttribute('aria-hidden', 'true');
        const typeToggleText = document.createElement('span');
        typeToggleText.textContent = 'Change input type';
        typeToggleLabel.append(typeToggle, typeToggleTrack, typeToggleText);
        recordForm.closest('.master-form-section')?.querySelector('.master-section-title')?.append(typeToggleLabel);
        typeToggle.addEventListener('change', () => {
            recordForm.querySelectorAll('.element-type-controls').forEach((controls) => {
                controls.hidden = !typeToggle.checked;
            });
        });

        recordForm.querySelectorAll('.dynamic-field').forEach((container) => {
        let control = container.querySelector('input, select, textarea');
        if (!control) return;
        const isChoice = control.tagName === 'SELECT';
        const isText = control.tagName === 'TEXTAREA' || (control.tagName === 'INPUT' && control.type === 'text');
        if (!isChoice && !isText) return;
        const original = control.cloneNode(true);
        const fieldName = control.name;
        const label = container.querySelector('label');
        const preferenceKey = `schoolhub-field:${recordForm.dataset.recordScope}:${fieldName}`;
        const typeControls = document.createElement('div');
        typeControls.className = 'element-type-controls';
        typeControls.hidden = true;
        const selectorLabel = document.createElement('label');
        selectorLabel.className = 'element-type-label';
        selectorLabel.textContent = 'Input type';
        const selector = document.createElement('select');
        selector.className = 'element-type-select';
        selector.setAttribute('aria-label', selectorLabel.textContent);
        const choices = isChoice ? [['select', 'Dropdown'], ['radio', 'Radio choices']] : [['text', 'Text box'], ['textarea', 'Multiline text']];
        choices.forEach(([value, name]) => selector.add(new Option(name, value)));
        selectorLabel.append(selector);
        typeControls.append(selectorLabel);
        container.append(typeControls);
        typeToggleLabel.hidden = false;
        const applyType = (type) => {
            const value = control.dataset.radioGroup ? control.querySelector('input:checked')?.value || '' : control.value;
            let replacement;
            if (isChoice && type === 'radio') {
                replacement = document.createElement('div');
                replacement.className = 'record-radio-group';
                replacement.dataset.radioGroup = 'true';
                replacement.setAttribute('role', 'radiogroup');
                replacement.setAttribute('aria-label', label.textContent);
                Array.from(original.options).forEach((option) => {
                    const item = document.createElement('label');
                    const radio = document.createElement('input');
                    radio.type = 'radio';
                    radio.name = fieldName;
                    radio.value = option.value;
                    radio.checked = option.value === value;
                    radio.required = original.required;
                    radio.disabled = option.disabled;
                    item.append(radio, document.createTextNode(option.textContent));
                    replacement.append(item);
                });
            } else if (isText && type === 'textarea') {
                replacement = document.createElement('textarea');
                Array.from(original.attributes).forEach((attribute) => {
                    if (attribute.name !== 'type' && attribute.name !== 'value') replacement.setAttribute(attribute.name, attribute.value);
                });
                replacement.rows = 3;
                replacement.value = value;
            } else {
                replacement = original.cloneNode(true);
                replacement.value = value;
            }
            control.replaceWith(replacement);
            control = replacement;
        };
        selector.addEventListener('change', () => {
            applyType(selector.value);
            try { localStorage.setItem(preferenceKey, selector.value); } catch (error) {}
        });
        try {
            const saved = localStorage.getItem(preferenceKey);
            if (choices.some(([value]) => value === saved)) {
                selector.value = saved;
                applyType(saved);
            }
        } catch (error) {}
        });
    }
    const menu = document.querySelector('.mobile-menu');
    const sidebar = document.querySelector('.sidebar');
    const shell = document.querySelector('.app-shell');
    const mobileLayout = window.matchMedia('(max-width: 720px)');
    if (menu && sidebar && shell) {
        const updateMenuState = () => {
            const expanded = mobileLayout.matches
                ? sidebar.classList.contains('is-open')
                : !shell.classList.contains('sidebar-hidden');
            const label = expanded ? 'Hide sidebar' : 'Show sidebar';
            menu.setAttribute('aria-expanded', String(expanded));
            menu.setAttribute('aria-label', label);
            menu.title = label;
        };
        updateMenuState();
        menu.addEventListener('click', () => {
            if (mobileLayout.matches) {
                sidebar.classList.toggle('is-open');
            } else {
                shell.classList.toggle('sidebar-hidden');
            }
            updateMenuState();
        });
        sidebar.querySelector('.sidebar-close')?.addEventListener('click', () => {
            sidebar.classList.remove('is-open');
            updateMenuState();
            menu.focus();
        });
        mobileLayout.addEventListener('change', () => {
            sidebar.classList.remove('is-open');
            shell.classList.remove('sidebar-hidden');
            updateMenuState();
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
    const passwordResetForm = document.querySelector('[data-password-reset]');
    if (passwordResetForm) {
        const updateScope = () => {
            const scope = passwordResetForm.querySelector('input[name="reset_scope"]:checked')?.value;
            passwordResetForm.querySelectorAll('[data-reset-scope]').forEach((container) => {
                container.hidden = container.dataset.resetScope !== scope;
            });
        };
        passwordResetForm.querySelectorAll('input[name="reset_scope"]').forEach((input) => {
            input.addEventListener('change', updateScope);
        });
        updateScope();
    }
    const deleteDialog = document.querySelector('[data-delete-dialog]');
    const deleteDialogPanel = deleteDialog?.querySelector('.confirm-dialog');
    const deleteConfirmButton = deleteDialog?.querySelector('[data-delete-confirm]');
    const deleteCancelButton = deleteDialog?.querySelector('[data-delete-cancel]');
    const deleteForms = document.querySelectorAll('form[onsubmit*="confirm("]');
    let pendingDeleteForm = null;
    let deleteFocusOrigin = null;
    const closeDeleteDialog = () => {
        if (!deleteDialog || !pendingDeleteForm) return;
        deleteDialog.hidden = true;
        document.querySelector('.app-main')?.classList.remove('confirm-dialog-open');
        pendingDeleteForm = null;
        deleteFocusOrigin?.focus();
        deleteFocusOrigin = null;
    };
    if (deleteDialog && deleteDialogPanel && deleteConfirmButton && deleteCancelButton) {
        deleteForms.forEach((form) => {
            form.removeAttribute('onsubmit');
            form.addEventListener('submit', (event) => {
                event.preventDefault();
                pendingDeleteForm = form;
                deleteFocusOrigin = event.submitter || form.querySelector('button[type="submit"]');
                deleteDialog.hidden = false;
                document.querySelector('.app-main')?.classList.add('confirm-dialog-open');
                deleteConfirmButton.focus();
            });
        });
        deleteCancelButton.addEventListener('click', closeDeleteDialog);
        deleteDialog.addEventListener('click', (event) => {
            if (event.target === deleteDialog) closeDeleteDialog();
        });
        deleteConfirmButton.addEventListener('click', () => {
            if (pendingDeleteForm) HTMLFormElement.prototype.submit.call(pendingDeleteForm);
        });
        document.addEventListener('keydown', (event) => {
            if (deleteDialog.hidden) return;
            if (event.key === 'Escape') {
                event.preventDefault();
                closeDeleteDialog();
            } else if (event.key === 'Tab') {
                event.preventDefault();
                const activeButton = document.activeElement;
                if (event.shiftKey) {
                    (activeButton === deleteCancelButton ? deleteConfirmButton : deleteCancelButton).focus();
                } else {
                    (activeButton === deleteConfirmButton ? deleteCancelButton : deleteConfirmButton).focus();
                }
            }
        });
    }
});