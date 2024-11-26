document.getElementById('theme-toggle').addEventListener('click', function() {
    const themeStyle = document.getElementById('theme-style');
    if (themeStyle.getAttribute('href') === '{% static "myapp/css/light.css" %}') {
        themeStyle.setAttribute('href', '{% static "myapp/css/dark.css" %}');
        this.textContent = 'Switch to Light Mode';
        localStorage.setItem('theme', 'dark');
    } else {
        themeStyle.setAttribute('href', '{% static "myapp/css/light.css" %}');
        this.textContent = 'Switch to Dark Mode';
        localStorage.setItem('theme', 'light');
    }
});

// Load the user's theme preference on page load
window.onload = function() {
    const theme = localStorage.getItem('theme');
    if (theme) {
        const themeStyle = document.getElementById('theme-style');
        themeStyle.setAttribute('href', theme === 'dark' ? '{% static "myapp/css/dark.css" %}' : '{% static "myapp/css/light.css" %}');
        document.getElementById('theme-toggle').textContent = theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
    }
};