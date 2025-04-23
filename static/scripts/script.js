/// Show/hide password functions
// Declare variables and link to HTML elements
let togglePassword = document.getElementById('togglePassword');
let toggleRePassword = document.getElementById('toggleRePassword');
let initialPasswordField = document.getElementById('floatingPassword');
let confirmPasswordField = document.getElementById('floatingPassword2');

// Toggle initial password visibility 
togglePassword.addEventListener('click', function () {
    let type = initialPasswordField.type === 'password' ? 'text' : 'password';
    initialPasswordField.type = type;
    togglePassword.textContent = type === 'password' ? 'Show Password' : 'Hide Password';
});

// Toggle re-enter password visibility
toggleRePassword.addEventListener('click', function () {
    let type = confirmPasswordField.type === 'password' ? 'text' : 'password';
    confirmPasswordField.type = type;
    toggleRePassword.textContent = type === 'password' ? 'Show Password' : 'Hide Password';
});
/// End of show/hide pwd funcs

// Tooltip
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))