// Declare variables and link to HTML elements
let togglePassword = document.getElementById('togglePassword');
let toggleRePassword = document.getElementById('toggleRePassword');
let passwordField = document.getElementById('floatingPassword');
let passwordIcon = document.getElementById('passwordIcon');

// Toggle button func (enter pwd)
togglePassword.addEventListener('click', function () {
    // Toggle the type attribute
    let type = passwordField.type === 'password' ? 'text' : 'password';
    passwordField.type = type;

    // Change button text based on visibility
    togglePassword.textContent = isPassword ? 'Hide Password' : 'Show Password';
});

// Toggle button func (re-enter pwd)
toggleRePassword.addEventListener('click', function () {
    // Toggle the type attribute
    let type = passwordField.type === 'password' ? 'text' : 'password';
    passwordField.type = type;

    // Change button text based on visibility
    togglePassword.textContent = isPassword ? 'Hide Password' : 'Show Password';
});