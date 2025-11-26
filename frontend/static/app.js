const API_BASE = '/api';

// State
let providers = [];
let projects = [];
let apiKeys = [];
let currentConversation = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupEventListeners();
    loadProviders();
    loadConversations();
});

// Tab Management
function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === tabName);
    });

    // Load data for the tab
    if (tabName === 'projects') loadProjects();
    if (tabName === 'api-keys') loadAPIKeys();
    if (tabName === 'import') loadImportJobs();
}

// Event Listeners
function setupEventListeners() {
    // Filters
    document.getElementById('apply-filters').addEventListener('click', loadConversations);

    // Back button
    document.getElementById('back-btn').addEventListener('click', () => {
        document.getElementById('conversation-detail').style.display = 'none';
        document.getElementById('conversation-list').style.display = 'block';
        currentConversation = null;
    });

    // Projects
    document.getElementById('add-project-btn').addEventListener('click', () => {
        document.getElementById('add-project-form').style.display = 'flex';
    });
    document.getElementById('cancel-project-btn').addEventListener('click', () => {
        document.getElementById('add-project-form').style.display = 'none';
    });
    document.getElementById('save-project-btn').addEventListener('click', createProject);

    // API Keys
    document.getElementById('add-api-key-btn').addEventListener('click', () => {
        document.getElementById('add-api-key-form').style.display = 'flex';
    });
    document.getElementById('cancel-api-key-btn').addEventListener('click', () => {
        document.getElementById('add-api-key-form').style.display = 'none';
    });
    document.getElementById('save-api-key-btn').addEventListener('click', createAPIKey);

    // Import
    document.getElementById('start-import-btn').addEventListener('click', () => {
        loadProvidersForImport();
        document.getElementById('start-import-form').style.display = 'flex';
    });
    document.getElementById('cancel-import-btn').addEventListener('click', () => {
        document.getElementById('start-import-form').style.display = 'none';
    });
    document.getElementById('run-import-btn').addEventListener('click', startImport);
    document.getElementById('import-provider').addEventListener('change', loadAPIKeysForProvider);
}

// API Calls
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        alert('An error occurred. Please check the console for details.');
        throw error;
    }
}

// Providers
async function loadProviders() {
    providers = await apiCall('/providers');
    updateProviderFilters();
}

function updateProviderFilters() {
    const filter = document.getElementById('provider-filter');
    filter.innerHTML = '<option value="">All Providers</option>';
    providers.forEach(p => {
        filter.innerHTML += `<option value="${p.id}">${p.display_name}</option>`;
    });

    // Also update API key form
    const apiKeyProvider = document.getElementById('api-key-provider');
    apiKeyProvider.innerHTML = '<option value="">Select Provider...</option>';
    providers.forEach(p => {
        apiKeyProvider.innerHTML += `<option value="${p.id}">${p.display_name}</option>`;
    });
}

// Conversations
async function loadConversations() {
    const search = document.getElementById('search').value;
    const providerId = document.getElementById('provider-filter').value;
    const projectId = document.getElementById('project-filter').value;

    let url = '/conversations?page=1&page_size=50';
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (providerId) url += `&provider_id=${providerId}`;
    if (projectId) url += `&project_id=${projectId}`;

    const conversations = await apiCall(url);
    renderConversations(conversations);
}

function renderConversations(conversations) {
    const list = document.getElementById('conversation-list');

    if (conversations.length === 0) {
        list.innerHTML = '<p class="loading">No conversations found.</p>';
        return;
    }

    list.innerHTML = conversations.map(conv => `
        <div class="conversation-item" onclick="loadConversationDetail('${conv.id}')">
            <div class="conversation-title">${conv.title || 'Untitled Conversation'}</div>
            <div class="conversation-meta">
                <span>📅 ${conv.started_at ? new Date(conv.started_at).toLocaleDateString() : 'Unknown date'}</span>
                <span>💬 ${conv.message_count} messages</span>
                ${conv.has_artifacts ? '<span>📎 Has attachments</span>' : ''}
                ${conv.projects.length > 0 ? `<span>🏷️ ${conv.projects.join(', ')}</span>` : ''}
            </div>
        </div>
    `).join('');
}

async function loadConversationDetail(conversationId) {
    const conversation = await apiCall(`/conversations/${conversationId}`);
    currentConversation = conversation;
    renderConversationDetail(conversation);

    document.getElementById('conversation-list').style.display = 'none';
    document.getElementById('conversation-detail').style.display = 'block';
}

function renderConversationDetail(conv) {
    const provider = providers.find(p => p.id === conv.provider_id);
    const content = document.getElementById('conversation-content');

    let html = `
        <div class="conversation-header">
            <h2>${conv.title || 'Untitled Conversation'}</h2>
            <div class="conversation-meta">
                <span><strong>Provider:</strong> ${provider?.display_name || 'Unknown'}</span>
                <span><strong>Started:</strong> ${conv.started_at ? new Date(conv.started_at).toLocaleString() : 'Unknown'}</span>
                ${conv.ended_at ? `<span><strong>Ended:</strong> ${new Date(conv.ended_at).toLocaleString()}</span>` : ''}
            </div>
            <button onclick="exportConversation('${conv.id}')" class="btn-primary" style="margin-top: 15px;">
                📥 Export to Markdown
            </button>
        </div>
        <hr style="margin: 20px 0;">
        <div class="messages">
    `;

    conv.messages.forEach(msg => {
        html += `
            <div class="message ${msg.role}">
                <div class="message-role">${msg.role.toUpperCase()}</div>
                <div class="message-content">${escapeHtml(msg.content)}</div>
            </div>
        `;
    });

    html += '</div>';

    if (conv.artifacts.length > 0) {
        html += '<hr style="margin: 20px 0;"><h3>Attachments</h3><div class="artifacts">';
        conv.artifacts.forEach(art => {
            const statusClass = art.download_status === 'success' ? 'success' :
                               art.download_status === 'error' ? 'error' : 'warning';
            html += `
                <div class="list-item">
                    <div>
                        <strong>${art.filename || 'Unknown file'}</strong>
                        <span class="badge ${statusClass}">${art.download_status}</span>
                        <p>${art.artifact_type} ${art.mime_type ? `(${art.mime_type})` : ''}</p>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }

    content.innerHTML = html;
}

async function exportConversation(conversationId) {
    window.location.href = `${API_BASE}/conversations/${conversationId}/export-markdown`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Projects
async function loadProjects() {
    projects = await apiCall('/projects');
    renderProjects();
    updateProjectFilters();
}

function renderProjects() {
    const list = document.getElementById('projects-list');

    if (projects.length === 0) {
        list.innerHTML = '<p class="loading">No projects yet. Create one to get started!</p>';
        return;
    }

    list.innerHTML = projects.map(proj => `
        <div class="list-item">
            <div class="list-item-info">
                <h3>${proj.name}</h3>
                <p>${proj.description || 'No description'}</p>
                <small>Created: ${new Date(proj.created_at).toLocaleDateString()}</small>
            </div>
            <div class="list-item-actions">
                <button class="btn-secondary" onclick="deleteProject('${proj.id}')">Delete</button>
            </div>
        </div>
    `).join('');
}

function updateProjectFilters() {
    const filter = document.getElementById('project-filter');
    filter.innerHTML = '<option value="">All Projects</option>';
    projects.forEach(p => {
        filter.innerHTML += `<option value="${p.id}">${p.name}</option>`;
    });
}

async function createProject() {
    const name = document.getElementById('project-name').value.trim();
    const description = document.getElementById('project-description').value.trim();

    if (!name) {
        alert('Please enter a project name');
        return;
    }

    await apiCall('/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description: description || null })
    });

    document.getElementById('add-project-form').style.display = 'none';
    document.getElementById('project-name').value = '';
    document.getElementById('project-description').value = '';
    loadProjects();
}

async function deleteProject(projectId) {
    if (!confirm('Are you sure you want to delete this project?')) return;

    await apiCall(`/projects/${projectId}`, { method: 'DELETE' });
    loadProjects();
}

// API Keys
async function loadAPIKeys() {
    apiKeys = await apiCall('/api-keys');
    renderAPIKeys();
}

function renderAPIKeys() {
    const list = document.getElementById('api-keys-list');

    if (apiKeys.length === 0) {
        list.innerHTML = '<p class="loading">No API keys configured.</p>';
        return;
    }

    list.innerHTML = apiKeys.map(key => {
        const provider = providers.find(p => p.id === key.provider_id);
        const statusClass = key.is_active ? 'success' : 'warning';
        return `
            <div class="list-item">
                <div class="list-item-info">
                    <h3>${key.label}</h3>
                    <p>${provider?.display_name || 'Unknown Provider'}</p>
                    <small>Created: ${new Date(key.created_at).toLocaleDateString()}</small>
                    ${key.last_used_at ? `<small>Last used: ${new Date(key.last_used_at).toLocaleDateString()}</small>` : ''}
                    <span class="badge ${statusClass}">${key.is_active ? 'Active' : 'Inactive'}</span>
                </div>
                <div class="list-item-actions">
                    <button class="btn-secondary" onclick="toggleAPIKey('${key.id}', ${!key.is_active})">
                        ${key.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button class="btn-secondary" onclick="deleteAPIKey('${key.id}')">Delete</button>
                </div>
            </div>
        `;
    }).join('');
}

async function createAPIKey() {
    const providerId = document.getElementById('api-key-provider').value;
    const label = document.getElementById('api-key-label').value.trim();
    const apiKeyValue = document.getElementById('api-key-value').value.trim();

    if (!providerId || !label || !apiKeyValue) {
        alert('Please fill in all fields');
        return;
    }

    await apiCall('/api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            provider_id: providerId,
            label,
            api_key_value: apiKeyValue
        })
    });

    document.getElementById('add-api-key-form').style.display = 'none';
    document.getElementById('api-key-provider').value = '';
    document.getElementById('api-key-label').value = '';
    document.getElementById('api-key-value').value = '';
    loadAPIKeys();
}

async function toggleAPIKey(keyId, isActive) {
    await apiCall(`/api-keys/${keyId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: isActive })
    });
    loadAPIKeys();
}

async function deleteAPIKey(keyId) {
    if (!confirm('Are you sure you want to delete this API key?')) return;

    await apiCall(`/api-keys/${keyId}`, { method: 'DELETE' });
    loadAPIKeys();
}

// Import Jobs
async function loadImportJobs() {
    const jobs = await apiCall('/import-jobs');
    renderImportJobs(jobs);
}

function renderImportJobs(jobs) {
    const list = document.getElementById('import-jobs-list');

    if (jobs.length === 0) {
        list.innerHTML = '<p class="loading">No import jobs yet.</p>';
        return;
    }

    list.innerHTML = jobs.map(job => {
        const provider = providers.find(p => p.id === job.provider_id);
        const statusClass = job.status === 'success' ? 'success' :
                          job.status === 'running' ? 'running' :
                          job.status === 'partial' ? 'warning' : 'error';

        return `
            <div class="list-item">
                <div class="list-item-info">
                    <h3>${provider?.display_name || 'Unknown Provider'}</h3>
                    <span class="badge ${statusClass}">${job.status.toUpperCase()}</span>
                    <p>${job.summary || 'In progress...'}</p>
                    <small>Started: ${new Date(job.started_at).toLocaleString()}</small>
                    ${job.finished_at ? `<small>Finished: ${new Date(job.finished_at).toLocaleString()}</small>` : ''}
                    <p><strong>Stats:</strong> ${job.conversations_imported} conversations, ${job.messages_imported} messages, ${job.artifacts_imported} artifacts</p>
                    ${job.error_details ? `<p class="note">${job.error_details}</p>` : ''}
                </div>
            </div>
        `;
    }).join('');
}

function loadProvidersForImport() {
    const select = document.getElementById('import-provider');
    select.innerHTML = '<option value="">Select Provider...</option>';
    providers.forEach(p => {
        select.innerHTML += `<option value="${p.id}">${p.display_name}</option>`;
    });
}

async function loadAPIKeysForProvider() {
    const providerId = document.getElementById('import-provider').value;
    if (!providerId) return;

    const keys = apiKeys.filter(k => k.provider_id === providerId && k.is_active);
    const select = document.getElementById('import-api-key');
    select.innerHTML = '<option value="">Select API Key...</option>';
    keys.forEach(k => {
        select.innerHTML += `<option value="${k.id}">${k.label}</option>`;
    });
}

async function startImport() {
    const providerId = document.getElementById('import-provider').value;
    const apiKeyId = document.getElementById('import-api-key').value;

    if (!providerId || !apiKeyId) {
        alert('Please select both provider and API key');
        return;
    }

    await apiCall('/import-jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: providerId, api_key_id: apiKeyId })
    });

    document.getElementById('start-import-form').style.display = 'none';
    loadImportJobs();
}
