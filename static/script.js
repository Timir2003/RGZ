// Проверяем авторизацию
async function checkAuth() {
    const res = await fetch('/api/check');
    const data = await res.json();
    if (data.authenticated) {
        document.getElementById('username').textContent = data.username;
        document.getElementById('logoutBtn').style.display = 'block';
    }
}

// Вход
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    const res = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    
    const result = await res.json();
    document.getElementById('message').textContent = result.message;
    document.getElementById('message').className = result.success ? 'success' : 'error';
    
    if (result.success) {
        setTimeout(() => window.location.href = '/resources', 1000);
    }
});

// Выход
async function logout() {
    await fetch('/api/logout', {method: 'POST'});
    window.location.href = '/';
}

// Загрузка материалов
async function loadResources() {
    const res = await fetch('/api/resources');
    const data = await res.json();
    
    const container = document.getElementById('resourcesList');
    if (!data.resources || data.resources.length === 0) {
        container.innerHTML = '<p>Нет доступных материалов</p>';
        return;
    }
    
    container.innerHTML = data.resources.map(r => `
        <div class="resource-card">
            <h3>${r.name}</h3>
            <p>Уровень доступа: ${r.access_level}</p>
            <p>Время доступа: ${r.available_hours}</p>
            <a href="/resource/${r.id}">Подробнее</a>
        </div>
    `).join('');
}

// Инициализация
if (window.location.pathname === '/resources') {
    loadResources();
}
checkAuth();