const container = document.getElementById('inner-container-form');
const registerBtn = document.getElementById('register');
const loginBtn = document.getElementById('login');
const btn = document.getElementById('but');

registerBtn.addEventListener('click', () => {
    container.classList.add("active");
});

loginBtn.addEventListener('click', () => {
    container.classList.remove("active");
});