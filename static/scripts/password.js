let togglePassword = document.getElementById('togglePassword');
let toggleRePassword = document.getElementById('toggleRePassword');
let initialPasswordField = document.getElementById('floatingPassword');
let confirmPasswordField = document.getElementById('floatingPassword2');

// Toggle initial password visibility 
togglePassword.addEventListener('click', function () {
    let icon = togglePassword.querySelector('i');
    let type = initialPasswordField.type === 'password' ? 'text' : 'password';
    initialPasswordField.type = type;
    icon.classList.toggle('bi-eye');
    icon.classList.toggle('bi-eye-slash');
});

// Toggle re-enter password visibility
toggleRePassword.addEventListener('click', function () {
    let icon = toggleRePassword.querySelector('i');
    let type = confirmPasswordField.type === 'password' ? 'text' : 'password';
    confirmPasswordField.type = type;
    icon.classList.toggle('bi-eye');
    icon.classList.toggle('bi-eye-slash');
});
