document.querySelectorAll('.student-sibling-lookup').forEach((button) => {
    button.addEventListener('click', async () => {
        const container = button.closest('[data-field]');
        const input = container.querySelector('input');
        const message = container.querySelector('[role="status"]');
        const form = button.closest('form');
        const prefix = input.name.replace('_scholar_', '_');
        const parts = prefix.split('_');
        const kind = parts[0];
        const number = parts[1];
        message.textContent = '';
        try {
            const url = new URL(form.dataset.siblingUrl, window.location.origin);
            url.searchParams.set('scholar_number', input.value);
            const response = await fetch(url, {headers: {'Accept': 'application/json'}});
            const result = await response.json();
            if (!response.ok) {
                message.textContent = result.error || 'Unable to find student.';
                return;
            }
            form.elements[`${kind}_name_${number}`].value = result.name || '';
            form.elements[`${kind}_class_${number}`].value = result.class_id || '';
            form.elements[`${kind}_section_${number}`].value = result.section || '';
        } catch (error) {
            message.textContent = 'Unable to find student.';
        }
    });
});

const registrationForm = document.querySelector('.enrollment-form[data-sibling-url]');
if (registrationForm) {
    const sameAddress = registrationForm.elements.same_address;
    const copyAddress = () => {
        if (!sameAddress || !sameAddress.checked) return;
        ['address_1', 'address_2', 'address_3', 'city', 'state', 'country', 'postal_code', 'phone'].forEach((suffix) => {
            registrationForm.elements[`communication_${suffix}`].value = registrationForm.elements[`permanent_${suffix}`].value;
        });
    };
    if (sameAddress) {
        sameAddress.addEventListener('change', copyAddress);
        registrationForm.querySelectorAll('[name^="permanent_"]').forEach((input) => input.addEventListener('change', copyAddress));
    }
    const classSelect = registrationForm.elements.class_id;
    const ipField = registrationForm.querySelector('[data-field="with_ip"]');
    if (classSelect && ipField) {
        const updateIp = () => { ipField.hidden = !['14', '15'].includes(classSelect.value); };
        updateIp();
        classSelect.addEventListener('change', () => {
            updateIp();
            registrationForm.requestSubmit(registrationForm.querySelector('[value="refresh"]'));
        });
    }
}