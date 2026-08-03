// ======================================
// Auth Forms JS (login / register)
// ======================================

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("loginForm");
    const registerForm = document.getElementById("registerForm");

    if (loginForm) {
        loginForm.addEventListener("submit", handleLoginSubmit);
    }

    if (registerForm) {
        registerForm.addEventListener("submit", handleRegisterSubmit);
    }
});

function handleLoginSubmit(event) {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    if (!username || !password) {
        event.preventDefault();
        alert("Please enter both username and password.");
    }
}

function handleRegisterSubmit(event) {
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    if (!username || !email || !password) {
        event.preventDefault();
        alert("All fields are required.");
        return;
    }

    if (password.length < 6) {
        event.preventDefault();
        alert("Password must be at least 6 characters long.");
        return;
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(email)) {
        event.preventDefault();
        alert("Please enter a valid email address.");
    }
}
