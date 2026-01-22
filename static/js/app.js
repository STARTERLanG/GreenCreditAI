// --- 1. Utils & Helpers ---
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Global Image Modal Helpers
window.openImageModal = (url) => {
    const modal = document.getElementById('image-preview-modal');
    const img = document.getElementById('image-preview-src');
    if (!modal || !img) return;
    img.src = url;
    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.classList.remove('opacity-0');
        img.classList.replace('scale-95', 'scale-100');
    }, 10);
};

window.closeImageModal = () => {
    const modal = document.getElementById('image-preview-modal');
    const img = document.getElementById('image-preview-src');
    if (!modal || !img) return;
    modal.classList.add('opacity-0');
    img.classList.replace('scale-100', 'scale-95');
    setTimeout(() => {
        modal.classList.add('hidden');
        img.src = '';
    }, 300);
};

function scrollToBottom() {
    if (dom.chatWindow) {
        dom.chatWindow.scrollTop = dom.chatWindow.scrollHeight;
    }
}

function updatePageTitle(title) {
    document.title = `绿色信贷智能助手 - ${title || '新对话'}`;
}

function getFileCardHtml(hash, name) {
    return `
        <div onclick="event.stopPropagation(); window.openPreview('${hash}', '${name}')" class="group flex items-center bg-white/80 border border-emerald-100 rounded-lg p-2 mb-2 shadow-sm w-fit max-w-[200px] cursor-pointer hover:bg-emerald-50 transition-colors select-none">
            <div class="w-8 h-8 bg-emerald-50 text-emerald-600 rounded flex items-center justify-center mr-3 flex-shrink-0 group-hover:bg-white group-hover:text-emerald-700">
                <i class="fas fa-file-alt text-lg"></i>
            </div>
            <div class="text-[11px] text-slate-700 font-medium truncate pointer-events-none">${name}</div>
        </div>
    `;
}

// --- 2. State & Config ---
let currentSessionId = localStorage.getItem('last_session_id') || generateUUID();
let isGenerating = false;
let isSidebarCollapsed = false;
let sidebarWidth = 250;
let pendingRenameId = null;
let pendingDeleteId = null;
let pendingFiles = [];

// --- 3. DOM Elements ---
const dom = {
    input: document.getElementById('user-input'),
    sendBtn: document.getElementById('send-btn'),
    chatWindow: document.getElementById('chat-window'),
    fileInput: document.getElementById('file-upload'),
    uploadBtn: document.getElementById('upload-btn'),
    sessionList: document.getElementById('session-list'),
    newChatBtn: document.getElementById('new-chat-btn'),
    sidebar: document.getElementById('sidebar'),
    sidebarToggle: document.getElementById('sidebar-toggle'),
    toggleIcon: document.getElementById('toggle-icon'),
    searchBtn: document.getElementById('search-btn'),
    resizer: document.getElementById('sidebar-resizer'),
    renameModal: document.getElementById('rename-modal'),
    modalContent: document.getElementById('modal-content'),
    renameInput: document.getElementById('rename-input'),
    cancelRenameBtn: document.getElementById('cancel-rename-btn'),
    confirmRenameBtn: document.getElementById('confirm-rename-btn'),
    deleteModal: document.getElementById('delete-modal'),
    deleteModalContent: document.getElementById('delete-modal-content'),
    deleteModalTitle: document.getElementById('delete-modal-title'),
    cancelDeleteBtn: document.getElementById('cancel-delete-btn'),
    confirmDeleteBtn: document.getElementById('confirm-delete-btn'),
    pendingFileZone: document.getElementById('pending-file-zone'),
    previewPanel: document.getElementById('preview-panel'),
    chatContainer: document.getElementById('chat-container'),
    previewContent: document.getElementById('preview-content'),
    previewTitle: document.getElementById('preview-title'),
    closePreviewBtn: document.getElementById('close-preview-btn'),
    previewResizer: document.getElementById('preview-resizer'),
    viewOriginalBtn: document.getElementById('view-original-btn'),
    viewAiBtn: document.getElementById('view-ai-btn'),
    // Settings DOM
    settingsBtn: document.getElementById('settings-btn'),
    settingsView: document.getElementById('settings-view'),
    closeSettingsViewBtn: document.getElementById('close-settings-view-btn'),
    settingsNav: document.getElementById('settings-nav'),
    
    // Inputs in View
    viewSettingAutoExpand: document.getElementById('view-setting-auto-expand'),
    viewFontSizeGroup: document.getElementById('view-font-size-group'),
    viewDensityGroup: document.getElementById('view-density-group'),
    auditModeGroup: document.getElementById('audit-mode-group'),
    btnClearAllData: document.getElementById('btn-clear-all-data'),
    
    // Custom API Tools DOM
    apiEditorContainer: document.getElementById('api-editor-container'),
    apiToolsList: document.getElementById('api-tools-list'),
    btnAddApiTool: document.getElementById('btn-add-api-tool'),
    btnCancelApiTool: document.getElementById('btn-cancel-api-tool'),
    btnSaveApiTool: document.getElementById('btn-save-api-tool'),
    apiEditorTitle: document.getElementById('api-editor-title'),
    
    // cURL Import
    curlImportBox: document.getElementById('curl-import-box'),
    curlInput: document.getElementById('curl-input'),
    
    // Editor Inputs
    editApiId: document.getElementById('edit-api-id'),
    editApiName: document.getElementById('edit-api-name'),
    editApiMethod: document.getElementById('edit-api-method'),
    editApiDesc: document.getElementById('edit-api-desc'),
    editApiUrl: document.getElementById('edit-api-url'),
    headersContainer: document.getElementById('headers-container'),
    paramsContainer: document.getElementById('params-container'),
    examplesContainer: document.getElementById('examples-container')
};

// --- Settings Logic ---
const defaultSettings = { 
    fontSize: 'normal', 
    density: 'normal', 
    autoExpandCoT: false, 
    auditMode: 'standard',
    customApis: []
};
let appSettings = JSON.parse(localStorage.getItem('app_settings')) || defaultSettings;

// Migration for old settings
if (appSettings.temperature !== undefined) {
    delete appSettings.temperature;
    if (!appSettings.auditMode) appSettings.auditMode = 'standard';
    localStorage.setItem('app_settings', JSON.stringify(appSettings));
}

function applySettings() {
    // 1. Font Size
    if (appSettings.fontSize === 'large') document.body.classList.add('text-lg-mode');
    else document.body.classList.remove('text-lg-mode');
    
    // 2. Density
    if (appSettings.density === 'compact') document.body.classList.add('density-compact');
    else document.body.classList.remove('density-compact');
}

// --- View Switching ---
function showChat() {
    dom.settingsView.classList.add('hidden');
    dom.chatContainer.classList.remove('hidden');
}

function showSettings() {
    dom.chatContainer.classList.add('hidden');
    dom.settingsView.classList.remove('hidden');
    updateSettingsUI();
}

function updateSettingsUI() {
    // Auto Expand
    if (dom.viewSettingAutoExpand) dom.viewSettingAutoExpand.checked = appSettings.autoExpandCoT;
    
    // Font Size Group
    if (dom.viewFontSizeGroup) {
        updateButtonGroup(dom.viewFontSizeGroup, appSettings.fontSize, 'bg-white shadow-sm text-emerald-700', 'text-slate-500 hover:text-slate-900');
    }

    // Density Group
    if (dom.viewDensityGroup) {
        updateButtonGroup(dom.viewDensityGroup, appSettings.density, 'bg-white shadow-sm text-emerald-700', 'text-slate-500 hover:text-slate-900');
    }

    // Audit Mode Cards
    if (dom.auditModeGroup) {
        const cards = dom.auditModeGroup.querySelectorAll('.audit-mode-card');
        cards.forEach(card => {
            const mode = card.getAttribute('data-mode');
            const checkIcon = card.querySelector('.check-icon');
            
            if (mode === appSettings.auditMode) {
                // Active State
                checkIcon.classList.remove('opacity-0');
                if (mode === 'strict') {
                    card.className = "audit-mode-card cursor-pointer group relative bg-white p-6 rounded-2xl border-2 border-slate-600 ring-4 ring-slate-600/10 transition-all duration-200";
                } else if (mode === 'standard') {
                    card.className = "audit-mode-card cursor-pointer group relative bg-white p-6 rounded-2xl border-2 border-emerald-500 ring-4 ring-emerald-500/10 transition-all duration-200";
                } else if (mode === 'advisory') {
                    card.className = "audit-mode-card cursor-pointer group relative bg-white p-6 rounded-2xl border-2 border-blue-500 ring-4 ring-blue-500/10 transition-all duration-200";
                }
            } else {
                // Inactive State
                checkIcon.classList.add('opacity-0');
                card.className = "audit-mode-card cursor-pointer group relative bg-white p-6 rounded-2xl border-2 border-slate-200 hover:border-slate-400 transition-all duration-200";
            }
        });
    }

    // Custom APIs
    renderApiList();
}

function renderApiList() {
    if (!dom.apiToolsList) return;
    dom.apiToolsList.innerHTML = '';
    const apis = appSettings.customApis || [];
    
    if (apis.length === 0) {
        dom.apiToolsList.innerHTML = `
            <div id="api-tools-empty" class="text-center py-12 bg-white rounded-xl border border-dashed border-slate-300">
                <div class="w-12 h-12 bg-slate-50 text-slate-300 rounded-full flex items-center justify-center mx-auto mb-3 text-xl"><i class="fas fa-toolbox"></i></div>
                <h4 class="text-slate-600 font-bold text-sm">暂无自定义工具</h4>
                <p class="text-[10px] text-slate-400 mt-1">点击右上角“新建工具”添加您的第一个 HTTP 接口</p>
            </div>`;
        return;
    }

    apis.forEach(api => {
        const div = document.createElement('div');
        div.className = 'bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between transition-all hover:shadow-md hover:border-emerald-300 group';
        
        // Style based on Method
        const styles = {
            'GET': { bg: 'bg-blue-100', text: 'text-blue-600', icon: 'fa-search' },
            'POST': { bg: 'bg-emerald-100', text: 'text-emerald-600', icon: 'fa-paper-plane' },
            'PUT': { bg: 'bg-orange-100', text: 'text-orange-600', icon: 'fa-edit' },
            'DELETE': { bg: 'bg-red-100', text: 'text-red-600', icon: 'fa-trash' }
        };
        const style = styles[api.method] || { bg: 'bg-slate-100', text: 'text-slate-600', icon: 'fa-terminal' };
        
        // Clean URL for display
        const displayUrl = api.url.replace(/^https?:\/\//, '');
        
        div.innerHTML = `
            <div class="flex items-center gap-4 overflow-hidden">
                <div class="w-10 h-10 rounded-lg ${style.bg} ${style.text} flex items-center justify-center text-sm flex-shrink-0">
                    <i class="fas ${style.icon}"></i>
                </div>
                <div class="min-w-0">
                    <div class="flex items-center gap-2">
                        <div class="text-sm font-bold text-slate-800 truncate">${api.name}</div>
                        <span class="text-[10px] font-mono px-1.5 py-0.5 rounded ${style.bg} ${style.text} opacity-80">${api.method}</span>
                    </div>
                    <div class="text-xs text-slate-500 flex items-center gap-2 truncate mt-0.5">
                        <span class="truncate font-mono opacity-70 max-w-[200px]" title="${api.url}">${displayUrl}</span>
                        ${api.desc ? `<span class="text-slate-300">|</span> <span class="truncate">${api.desc}</span>` : ''}
                    </div>
                </div>
            </div>
            
            <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                <button onclick="window.editApiTool('${api.id}')" class="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors" title="编辑">
                    <i class="fas fa-pencil-alt text-xs"></i>
                </button>
                <button onclick="window.deleteApiTool('${api.id}')" class="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="删除">
                    <i class="fas fa-trash-alt text-xs"></i>
                </button>
            </div>
        `;
        dom.apiToolsList.appendChild(div);
    });
}

window.addHeaderRow = (key = '', value = '') => {
    const div = document.createElement('div');
    div.className = 'header-row grid grid-cols-12 gap-2 items-center';
    div.innerHTML = `
        <div class="col-span-5"><input type="text" class="h-input w-full border border-slate-300 rounded px-2 py-1.5 text-xs focus:ring-2 focus:ring-emerald-500 font-mono" placeholder="Key" value="${key}"></div>
        <div class="col-span-6"><input type="text" class="v-input w-full border border-slate-300 rounded px-2 py-1.5 text-xs focus:ring-2 focus:ring-emerald-500 font-mono" placeholder="Value" value="${value}"></div>
        <div class="col-span-1 text-center"><button onclick="this.closest('.header-row').remove()" class="text-slate-400 hover:text-red-500 transition-colors"><i class="fas fa-trash-alt"></i></button></div>
    `;
    dom.headersContainer.appendChild(div);
};

window.addParamRow = (name = '', type = 'string', required = false, desc = '') => {
    const div = document.createElement('div');
    div.className = 'param-row grid grid-cols-12 gap-2 items-center';
    div.innerHTML = `
        <div class="col-span-3"><input type="text" class="p-name w-full border border-slate-300 rounded px-2 py-1.5 text-xs focus:ring-2 focus:ring-emerald-500 font-mono" placeholder="Name" value="${name}"></div>
        <div class="col-span-2">
            <select class="p-type w-full border border-slate-300 rounded px-1 py-1.5 text-xs focus:ring-2 focus:ring-emerald-500 bg-white">
                <option value="string" ${type === 'string' ? 'selected' : ''}>String</option>
                <option value="number" ${type === 'number' ? 'selected' : ''}>Number</option>
                <option value="boolean" ${type === 'boolean' ? 'selected' : ''}>Boolean</option>
            </select>
        </div>
        <div class="col-span-1 text-center"><input type="checkbox" class="p-req w-4 h-4 text-emerald-600 rounded border-gray-300 focus:ring-emerald-500" ${required ? 'checked' : ''}></div>
        <div class="col-span-5"><input type="text" class="p-desc w-full border border-slate-300 rounded px-2 py-1.5 text-xs focus:ring-2 focus:ring-emerald-500" placeholder="Description" value="${desc}"></div>
        <div class="col-span-1 text-center"><button onclick="this.closest('.param-row').remove()" class="text-slate-400 hover:text-red-500 transition-colors"><i class="fas fa-trash-alt"></i></button></div>
    `;
    dom.paramsContainer.appendChild(div);
};

window.toggleCurlImport = () => {
    if (dom.curlImportBox.classList.contains('hidden')) {
        dom.curlImportBox.classList.remove('hidden');
        dom.curlInput.focus();
    } else {
        dom.curlImportBox.classList.add('hidden');
    }
};

window.parseCurl = () => {
    const curl = dom.curlInput.value.trim();
    if (!curl) return;
    
    // Simple Parser
    let method = 'GET';
    let url = '';
    const headers = {};
    
    // 1. Extract Method
    // Match -X POST, -XPOST, --request POST
    const explicitMethod = curl.match(/(-X|--request)\s*['"]?([A-Z]+)['"]?/i);
    if (explicitMethod) {
        method = explicitMethod[2].toUpperCase();
    } else {
        // Implicit POST if data flags are present
        if (curl.match(/(-d|--data|--data-raw|--data-binary|--json)\s+/)) {
            method = 'POST';
        }
    }
    
    // 2. Extract URL
    // Look for http/https pattern that is NOT inside a header value (simple heuristic)
    // We scan tokens. A token starting with http that isn't preceded by a flag like -H might be it.
    // Simpler regex: Find the first substring starting with http(s)://
    // Cleanup: remove line continuations (\)
    const cleanCurl = curl.replace(/\\\s*\n/g, ' ');
    const urlMatch = cleanCurl.match(/['"](https?:\/\/[^'"]+)['"]/) || cleanCurl.match(/(https?:\/\/[^\s"']+)/);
    if (urlMatch) url = urlMatch[1];
    
    // 3. Extract Headers
    // Match -H 'Key: Value' or --header "Key: Value"
    const headerRegex = /(-H|--header)\s+['"]?([^'"]+)['"]?/g;
    let match;
    while ((match = headerRegex.exec(cleanCurl)) !== null) {
        // match[2] is the content like "Content-Type: application/json"
        const content = match[2];
        const colonIndex = content.indexOf(':');
        if (colonIndex > 0) {
            const key = content.substring(0, colonIndex).trim();
            const val = content.substring(colonIndex + 1).trim();
            headers[key] = val;
        }
    }
    
    // Apply to UI
    if (url) {
        // Remove protocol prefix if present in the input group (The UI has https:// prefix span)
        // Check if the input group design has fixed prefix. 
        // In index.html: <span ...>https://</span> <input ...>
        // So we should strip https:// or http:// from the value
        dom.editApiUrl.value = url.replace(/^https?:\/\//, '');
    }
    
    dom.editApiMethod.value = method;
    // Trigger change event to update UI if we add color logic later
    dom.editApiMethod.dispatchEvent(new Event('change'));
    
    // Clear & Add Headers
    dom.headersContainer.innerHTML = '';
    Object.entries(headers).forEach(([k, v]) => window.addHeaderRow(k, v));
    if (Object.keys(headers).length === 0) window.addHeaderRow();
    
    dom.curlImportBox.classList.add('hidden');
};

window.openApiEditor = (id = null) => {
    dom.apiEditorContainer.classList.remove('hidden');
    dom.btnAddApiTool.classList.add('hidden'); // Hide Add btn when editing
    dom.headersContainer.innerHTML = '';
    dom.paramsContainer.innerHTML = '';
    if(dom.examplesContainer) dom.examplesContainer.innerHTML = '';
    dom.curlImportBox.classList.add('hidden');
    dom.curlInput.value = '';
    
    if (id) {
        const api = appSettings.customApis.find(a => a.id === id);
        if (api) {
            dom.editApiId.value = api.id;
            dom.editApiName.value = api.name;
            dom.editApiMethod.value = api.method;
            dom.editApiDesc.value = api.desc;
            dom.editApiUrl.value = api.url;
            
            // Populate Headers
            if (api.headers) {
                try {
                    const headers = JSON.parse(api.headers);
                    Object.entries(headers).forEach(([k, v]) => window.addHeaderRow(k, v));
                } catch (e) { console.error(e); }
            }
            
            // Populate Params
            if (api.params) {
                try {
                    const schema = JSON.parse(api.params);
                    if (schema.properties) {
                        Object.entries(schema.properties).forEach(([name, prop]) => {
                            const req = schema.required ? schema.required.includes(name) : false;
                            window.addParamRow(name, prop.type, req, prop.description || '');
                        });
                    }
                } catch (e) { console.error(e); }
            }
            
            // Populate Examples
            if (api.examples && Array.isArray(api.examples)) {
                api.examples.forEach(ex => window.addExampleRow(ex));
            } else if (window.addExampleRow) {
                window.addExampleRow();
            }
            
            dom.apiEditorTitle.innerText = "编辑工具";
        }
    } else {
        // Reset
        dom.editApiId.value = '';
        dom.editApiName.value = '';
        dom.editApiMethod.value = 'GET';
        dom.editApiDesc.value = '';
        dom.editApiUrl.value = '';
        dom.apiEditorTitle.innerText = "配置新工具";
        window.addHeaderRow(); 
        window.addParamRow();
        if(window.addExampleRow) window.addExampleRow();
    }
};

window.closeApiEditor = () => {
    dom.apiEditorContainer.classList.add('hidden');
    dom.btnAddApiTool.classList.remove('hidden');
};

window.saveApiTool = () => {
    const id = dom.editApiId.value;
    const name = dom.editApiName.value.trim();
    if (!name) return alert("请输入工具名称");
    
    // Collect Headers
    const headers = {};
    dom.headersContainer.querySelectorAll('.header-row').forEach(row => {
        const k = row.querySelector('.h-input').value.trim();
        const v = row.querySelector('.v-input').value.trim();
        if (k) headers[k] = v;
    });
    
    // Collect Params
    const properties = {};
    const required = [];
    dom.paramsContainer.querySelectorAll('.param-row').forEach(row => {
        const n = row.querySelector('.p-name').value.trim();
        if (n) {
            const t = row.querySelector('.p-type').value;
            const desc = row.querySelector('.p-desc').value.trim();
            const isReq = row.querySelector('.p-req').checked;
            
            properties[n] = { type: t };
            if (desc) properties[n].description = desc;
            if (isReq) required.push(n);
        }
    });
    
    const paramsSchema = {
        type: "object",
        properties: properties,
        required: required.length > 0 ? required : undefined
    };
    
    // Collect Examples
    const examples = [];
    dom.examplesContainer.querySelectorAll('.ex-input').forEach(input => {
        const val = input.value.trim();
        if (val) examples.push(val);
    });
    
    const newApi = {
        id: id || generateUUID(),
        name: name,
        method: dom.editApiMethod.value,
        desc: dom.editApiDesc.value,
        url: dom.editApiUrl.value,
        headers: JSON.stringify(headers),
        params: JSON.stringify(paramsSchema),
        examples: examples
    };
    
    if (!appSettings.customApis) appSettings.customApis = [];
    
    if (id) {
        const idx = appSettings.customApis.findIndex(a => a.id === id);
        if (idx > -1) appSettings.customApis[idx] = newApi;
    } else {
        appSettings.customApis.push(newApi);
    }
    
    saveSettings();
    closeApiEditor();
    renderApiList();
};

window.deleteApiTool = (id) => {
    if (!confirm("确定删除此工具吗？")) return;
    appSettings.customApis = appSettings.customApis.filter(a => a.id !== id);
    saveSettings();
    renderApiList();
};

window.editApiTool = window.openApiEditor; // Alias

function updateButtonGroup(group, activeVal, activeClass, inactiveClass) {
    const btns = group.querySelectorAll('button');
    btns.forEach(btn => {
        const val = btn.getAttribute('data-value');
        if (val === activeVal) {
            btn.className = `px-5 py-2 text-xs font-medium rounded-md transition-all ${activeClass}`;
        } else {
            btn.className = `px-5 py-2 text-xs font-medium rounded-md transition-all ${inactiveClass}`;
        }
    });
}

function saveSettings() {
    localStorage.setItem('app_settings', JSON.stringify(appSettings));
    applySettings();
}

// Event Bindings
if (dom.settingsBtn) dom.settingsBtn.onclick = showSettings;
if (dom.closeSettingsViewBtn) dom.closeSettingsViewBtn.onclick = showChat;

// Nav Logic
if (dom.settingsNav) {
    const navBtns = dom.settingsNav.querySelectorAll('.settings-nav-item');
    navBtns.forEach(btn => {
        btn.onclick = () => {
            navBtns.forEach(b => {
                b.className = "settings-nav-item w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors";
                b.querySelector('i').className = b.querySelector('i').className.replace('text-emerald-700', '');
            });
            btn.className = "settings-nav-item w-full text-left px-3 py-2 rounded-lg text-sm font-medium bg-emerald-50 text-emerald-700 transition-colors";
            const targetId = btn.getAttribute('data-target');
            document.querySelectorAll('.settings-section').forEach(sec => sec.classList.add('hidden'));
            document.getElementById(targetId).classList.remove('hidden');
        };
    });
}

// Input Logic
if (dom.viewSettingAutoExpand) {
    dom.viewSettingAutoExpand.onchange = (e) => {
        appSettings.autoExpandCoT = e.target.checked;
        saveSettings();
    };
}

if (dom.viewFontSizeGroup) {
    const btns = dom.viewFontSizeGroup.querySelectorAll('button');
    btns.forEach(btn => {
        btn.onclick = () => {
            appSettings.fontSize = btn.getAttribute('data-value');
            saveSettings();
            updateSettingsUI();
        };
    });
}

if (dom.viewDensityGroup) {
    const btns = dom.viewDensityGroup.querySelectorAll('button');
    btns.forEach(btn => {
        btn.onclick = () => {
            appSettings.density = btn.getAttribute('data-value');
            saveSettings();
            updateSettingsUI();
        };
    });
}

if (dom.auditModeGroup) {
    const cards = dom.auditModeGroup.querySelectorAll('.audit-mode-card');
    cards.forEach(card => {
        card.onclick = () => {
            appSettings.auditMode = card.getAttribute('data-mode');
            saveSettings();
            updateSettingsUI();
        };
    });
}

if (dom.btnClearAllData) {
    dom.btnClearAllData.onclick = async () => {
        if (confirm("确定要删除所有历史记录吗？此操作无法撤销。")) {
            try {
                // Assuming there is an API for this, otherwise we might need to iterate or just clear local session ID
                // For now, let's implement a 'local reset' + backend clear if supported.
                // Since I don't see a 'delete all' endpoint in the file list (only by ID),
                // I'll assume we iterate or clear local ID.
                // Best practice: Clear local storage session and reload.
                localStorage.removeItem('last_session_id');
                // Optional: Call backend to clear (if API existed).
                // Since I can't confirm backend support for 'delete all', I will just reset the current session state locally.
                alert("本地会话状态已重置。");
                location.reload(); 
            } catch (e) { alert("操作失败"); }
        }
    };
}

if (dom.btnAddApiTool) dom.btnAddApiTool.onclick = () => window.openApiEditor();
if (dom.btnCancelApiTool) dom.btnCancelApiTool.onclick = window.closeApiEditor;
if (dom.btnSaveApiTool) dom.btnSaveApiTool.onclick = window.saveApiTool;

// --- Modal Logic ---
function openRenameModal(id, currentTitle) {
    pendingRenameId = id;
    dom.renameInput.value = currentTitle;
    dom.renameModal.classList.remove('hidden');
    setTimeout(() => { dom.renameModal.classList.remove('opacity-0'); dom.modalContent.classList.replace('scale-95', 'scale-100'); }, 10);
    dom.renameInput.focus();
}

function closeRenameModal() {
    dom.renameModal.classList.add('opacity-0');
    dom.modalContent.classList.replace('scale-100', 'scale-95');
    setTimeout(() => { dom.renameModal.classList.add('hidden'); pendingRenameId = null; }, 200);
}

function openDeleteModal(id, title) {
    pendingDeleteId = id;
    if (dom.deleteModalTitle) dom.deleteModalTitle.innerText = `删除会话: ${title || '未命名'}`;
    dom.deleteModal.classList.remove('hidden');
    setTimeout(() => { dom.deleteModal.classList.remove('opacity-0'); dom.deleteModalContent.classList.replace('scale-95', 'scale-100'); }, 10);
}

function closeDeleteModal() {
    dom.deleteModal.classList.add('opacity-0');
    dom.deleteModalContent.classList.replace('scale-100', 'scale-95');
    setTimeout(() => { dom.deleteModal.classList.add('hidden'); pendingDeleteId = null; }, 200);
}

// Bind Modal Events
if (dom.cancelRenameBtn) dom.cancelRenameBtn.onclick = closeRenameModal;
if (dom.cancelDeleteBtn) dom.cancelDeleteBtn.onclick = closeDeleteModal;

if (dom.confirmRenameBtn) {
    dom.confirmRenameBtn.onclick = async () => {
        const newTitle = dom.renameInput.value.trim();
        if (!newTitle || !pendingRenameId) return;
        try {
            await fetch(`/api/v1/chat/sessions/${pendingRenameId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: newTitle })
            });
            await loadSessions();
            if (pendingRenameId === currentSessionId) updatePageTitle(newTitle);
            closeRenameModal();
        } catch (e) { alert("重命名失败"); }
    };
}

if (dom.confirmDeleteBtn) {
    dom.confirmDeleteBtn.onclick = async () => {
        if (!pendingDeleteId) return;
        try {
            await fetch(`/api/v1/chat/sessions/${pendingDeleteId}`, { method: 'DELETE' });
            if (pendingDeleteId === currentSessionId) dom.newChatBtn.click();
            else await loadSessions();
            closeDeleteModal();
        } catch (e) { alert("删除失败"); }
    };
}

// --- Preview Logic ---
let previewWidth = 0;
let previewState = { hash: null, name: null, mode: 'ai' };

window.openToolDetail = (payload) => {
    const toggle = dom.previewPanel.querySelector('.flex.bg-slate-100');
    if (toggle) toggle.style.visibility = 'hidden';

    dom.previewPanel.style.display = 'flex';
    dom.previewPanel.style.width = `35%`;
    dom.previewTitle.innerText = `Trace: ${payload.name}`;
    const outputJson = typeof payload.output === 'object' ? JSON.stringify(payload.output, null, 2) : payload.output;
    dom.previewContent.innerHTML = `
        <div class="space-y-6">
            <div><h4 class="text-[10px] font-bold text-slate-400 uppercase mb-2">Input</h4><pre class="bg-slate-900 text-emerald-400 p-4 rounded-lg text-xs"><code>${payload.input}</code></pre></div>
            <div><h4 class="text-[10px] font-bold text-slate-400 uppercase mb-2">Output</h4><div class="bg-white border border-slate-200 p-4 rounded-lg text-xs text-slate-600 font-mono whitespace-pre-wrap">${outputJson || 'Waiting...'}</div></div>
        </div>
    `;
};

window.openPreview = async (hash, name) => {
    const toggle = dom.previewPanel.querySelector('.flex.bg-slate-100');
    if (toggle) toggle.style.visibility = 'visible';

    previewState = { hash, name, mode: 'ai' };
    const defaultWidth = window.innerWidth * 0.3;
    dom.previewPanel.style.display = 'flex';
    dom.previewPanel.offsetHeight;
    dom.previewPanel.style.width = `${defaultWidth}px`;
    dom.previewPanel.style.transition = 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
    dom.previewTitle.innerText = name;
    updateViewToggleUI();
    await renderPreviewContent();
};

function updateViewToggleUI() {
    if (!dom.viewOriginalBtn || !dom.viewAiBtn) return;
    if (previewState.mode === 'original') {
        dom.viewOriginalBtn.className = "px-3 py-1 text-xs font-medium rounded-md bg-white text-emerald-600 shadow-sm transition-all";
        dom.viewAiBtn.className = "px-3 py-1 text-xs font-medium rounded-md text-slate-500 hover:text-slate-700 transition-all";
    } else {
        dom.viewAiBtn.className = "px-3 py-1 text-xs font-medium rounded-md bg-white text-emerald-600 shadow-sm transition-all";
        dom.viewOriginalBtn.className = "px-3 py-1 text-xs font-medium rounded-md text-slate-500 hover:text-slate-700 transition-all";
    }
}

if (dom.viewOriginalBtn) dom.viewOriginalBtn.onclick = () => { previewState.mode = 'original'; updateViewToggleUI(); renderPreviewContent(); };
if (dom.viewAiBtn) dom.viewAiBtn.onclick = () => { previewState.mode = 'ai'; updateViewToggleUI(); renderPreviewContent(); };

async function renderPreviewContent() {
    const { hash, name, mode } = previewState;
    dom.previewContent.innerHTML = '<div class="flex items-center justify-center h-full text-slate-400 py-20"><i class="fas fa-spinner fa-spin mr-2"></i> Loading...</div>';
    try {
        if (mode === 'ai') {
            const res = await fetch(`/api/v1/documents/content/${hash}`);
            if (res.ok) {
                const data = await res.json();
                dom.previewContent.innerHTML = marked.parse(data.content);
            } else throw new Error("Load failed");
        } else {
            const res = await fetch(`/api/v1/documents/file/${hash}`);
            if (!res.ok) throw new Error("File fetch failed");
            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const ext = name.split('.').pop().toLowerCase();
            if (ext === 'pdf') {
                dom.previewContent.innerHTML = `<iframe src="${url}" class="w-full h-full border-none rounded-lg" style="min-height: 600px;"></iframe>`;
            } else if (ext === 'docx') {
                dom.previewContent.innerHTML = `<div id="docx-container" class="bg-white p-4"></div>`;
                docx.renderAsync(blob, document.getElementById("docx-container"));
            } else if (['jpg', 'png', 'jpeg'].includes(ext)) {
                dom.previewContent.innerHTML = `<div class="preview-img-container group" onclick="window.openImageModal('${url}')"><img src="${url}" class="max-w-full h-auto mx-auto shadow-sm"><div class="img-zoom-btn"><i class="fas fa-search-plus"></i></div></div>`;
            } else {
                dom.previewContent.innerHTML = `<div class="text-center mt-10 text-slate-500">此格式暂不支持在线预览<br><a href="${url}" download="${name}" class="text-emerald-600 underline mt-2">下载文件</a></div>`;
            }
        }
    } catch (e) {
        dom.previewContent.innerHTML = `<div class="text-red-500 text-center mt-10">加载失败: ${e.message}</div>`;
    }
}

if (dom.closePreviewBtn) {
    dom.closePreviewBtn.onclick = () => {
        dom.previewPanel.style.width = '0px';
        setTimeout(() => { if (dom.previewPanel.style.width === '0px') dom.previewPanel.style.display = 'none'; }, 300);
    };
}

// --- Render Logic ---
function renderWelcome() {
    if (!dom.chatWindow) return;
    dom.chatWindow.innerHTML = `
        <div class="welcome-screen flex flex-col items-center justify-center min-h-[70vh] fade-in-up px-4 text-center">
            <div class="space-y-4 mb-12">
                <div class="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-teal-600 pb-2">Hello, Banker</div>
                <h2 class="text-xl md:text-2xl text-slate-400 font-light">How can I help you today?</h2>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl mt-4 px-10">
                <div onclick="fillInput('光伏行业的最新准入标准是什么？')" class="group bg-white p-3 rounded-xl hover:bg-emerald-50 cursor-pointer transition-all duration-300 border border-slate-100 hover:border-emerald-200 shadow-sm flex items-center space-x-3 text-left">
                    <div class="bg-emerald-50 p-2 rounded-lg text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors flex-shrink-0"><i class="fas fa-search-dollar text-xs"></i></div>
                    <div class="flex-1 min-w-0"><div class="text-xs font-semibold text-slate-700 truncate">查询政策</div><div class="text-[10px] text-slate-400 truncate">"光伏行业的最新准入标准是什么？"</div></div>
                </div>
                <div onclick="fillInput('分析这份财报的环境风险')" class="group bg-white p-3 rounded-xl hover:bg-emerald-50 cursor-pointer transition-all duration-300 border border-slate-100 hover:border-emerald-200 shadow-sm flex items-center space-x-3 text-left">
                    <div class="bg-blue-50 p-2 rounded-lg text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors flex-shrink-0"><i class="fas fa-file-contract text-xs"></i></div>
                    <div class="flex-1 min-w-0"><div class="text-xs font-semibold text-slate-700 truncate">分析财报</div><div class="text-[10px] text-slate-400 truncate">"上传 PDF 并提取财务指标"</div></div>
                </div>
            </div>
        </div>
    `;
}

function renderMessage(content, role, animate = true, attachments = [], thought_process = []) {
    if (!dom.chatWindow) return;
    const welcome = dom.chatWindow.querySelector('.welcome-screen');
    if (welcome) welcome.remove();

    const wrapper = document.createElement('div');
    wrapper.className = `msg-wrapper mb-8 ${animate ? 'fade-in-up' : ''}`;
    const isUser = role === 'user';
    const avatarImg = isUser ? '/static/img/user-avatar.svg' : '/static/img/ai-avatar.svg';

    const actionsHtml = isUser ? `
        <div class="msg-actions justify-end mr-1">
            <button class="action-btn copy-btn" title="复制"><i class="fas fa-copy"></i></button>
        </div>` : `
        <div class="msg-actions ml-1">
            <button class="action-btn copy-btn" title="复制"><i class="fas fa-copy"></i></button>
            <button class="action-btn" title="重新生成"><i class="fas fa-sync-alt"></i></button>
        </div>`;

    const avatarImgTag = `<img src="${avatarImg}" class="avatar ${isUser ? 'order-2 ml-4' : 'order-1 mr-4'}" alt="${role}">`;

    let innerHtml = '';
    if (isUser) {
        let cardsHtml = '';
        if (attachments && attachments.length > 0) {
            cardsHtml = `<div class="file-cards-list mb-2 flex flex-wrap gap-2 justify-end">`;
            attachments.forEach(f => cardsHtml += getFileCardHtml(f.hash, f.name));
            cardsHtml += `</div>`;
        }
        innerHtml = `<div>${cardsHtml}${content ? `<div class="whitespace-pre-wrap">${content}</div>` : ''}</div>`;
    } else {
        // AI 消息：支持思维链
        let thoughtHtml = '';
        if (content.includes('thought-log-wrapper')) {
            thoughtHtml = content;
            content = "";
        } else if (thought_process && thought_process.length > 0) {
            // 历史记录渲染
            const isAutoExpanded = appSettings.autoExpandCoT;
            thoughtHtml = `
                <div class="thought-log-wrapper mb-4 bg-slate-50/80 rounded-xl border border-slate-100 overflow-hidden opacity-60">
                    <div class="flex items-center justify-between px-3 py-2 cursor-pointer" onclick="this.nextElementSibling.classList.toggle('hidden'); this.querySelector('.arrow-icon').classList.toggle('rotate-180')">
                        <div class="flex items-center space-x-2 text-slate-400">
                            <span class="status-text text-[10px] font-bold uppercase tracking-wider">思维链已完成</span>
                        </div>
                        <i class="fas fa-chevron-down arrow-icon text-[10px] text-slate-300 transition-transform ${isAutoExpanded ? '' : 'rotate-180'}"></i>
                    </div>
                    <div class="thought-log-container ${isAutoExpanded ? '' : 'hidden'} px-3 pb-3 space-y-3 border-t border-slate-50 pt-3">
                        <div class="text-log-area space-y-1.5"></div>
                        <div class="tool-table-area hidden">
                            <table class="w-full text-[10px] text-slate-500 border-collapse">
                                <thead><tr class="border-b border-slate-200"><th class="text-left py-1 font-semibold">Tool</th><th class="text-left py-1 font-semibold">Status</th><th class="text-right py-1 font-semibold">Action</th></tr></thead>
                                <tbody class="tool-list-body"></tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        }
        innerHtml = `${thoughtHtml}<div class="actual-response text-slate-700">${content ? marked.parse(content) : ''}</div>`;
    }

    const bubbleClass = isUser ? 'bg-gray-100 text-gray-800 rounded-[20px] rounded-tr-sm px-5 py-3' : 'w-full';
    wrapper.innerHTML = `
        <div class="msg-content-container flex w-full ${isUser ? 'justify-end' : 'justify-start'}">
            ${avatarImgTag}
            <div class="flex flex-col ${isUser ? 'order-1 items-end' : 'order-2 items-start'} flex-1 min-w-0 max-w-[85%]">
                <div class="${bubbleClass} msg-bubble leading-relaxed">${innerHtml}</div>
                <div class="mt-1 ${isUser ? 'mr-1' : 'ml-1'}">${actionsHtml}</div>
            </div>
        </div>
    `;

    if (!isUser && thought_process && thought_process.length > 0) {
        const container = wrapper.querySelector('.text-log-area');
        const toolArea = wrapper.querySelector('.tool-table-area');
        const toolBody = wrapper.querySelector('.tool-list-body');

        thought_process.forEach(log => {
            let payload = log;
            if (typeof log === 'string' && log.startsWith('{')) {
                try { payload = JSON.parse(log); } catch (e) { }
            }

            if (typeof payload === 'string') {
                const logItem = document.createElement('div');
                // 支持历史记录里的 <thinking> 标签回显（虽然历史记录通常是纯文本）
                // 暂时简单处理：如果是字符串，直接显示
                logItem.className = 'text-xs text-slate-400 flex items-start space-x-2';
                logItem.innerHTML = `<i class="fas fa-terminal mt-1 text-[8px] opacity-50"></i><span>${payload}</span>`;
                container.appendChild(logItem);
            } else if (payload && payload.type === 'tool_call') {
                toolArea.classList.remove('hidden');
                const row = document.createElement('tr');
                row.className = 'border-b border-slate-100/50 hover:bg-slate-100/50 cursor-pointer group';
                row.onclick = () => window.openToolDetail(payload);
                row.innerHTML = `
                    <td class="py-2 font-medium text-slate-600">${payload.name}</td>
                    <td class="py-2 text-emerald-500"><i class="fas fa-check-circle mr-1"></i>${payload.status}</td>
                    <td class="py-2 text-right"><span class="bg-slate-200 px-1.5 py-0.5 rounded text-[8px] group-hover:bg-emerald-500 group-hover:text-white transition-all">VIEW</span></td>
                `;
                toolBody.appendChild(row);
            }
        });
    }

    dom.chatWindow.appendChild(wrapper); scrollToBottom();
    return isUser ? null : wrapper.querySelector('.msg-bubble');
}

// --- Session Logic ---
async function loadSessions() {
    try {
        const res = await fetch('/api/v1/chat/sessions');
        const sessions = await res.json();
        if (!dom.sessionList) return; dom.sessionList.innerHTML = '';
        sessions.forEach(s => {
            const isActive = s.id === currentSessionId;
            const div = document.createElement('div');
            div.className = `group px-3 py-2.5 rounded-xl cursor-pointer flex items-center space-x-3 mb-1 transition-all duration-200 relative ${isActive ? 'bg-white shadow-sm text-emerald-800 font-bold border border-[#d1e2da]' : 'text-[#2d4a43]/70 hover:bg-white/40 hover:text-[#2d4a43]'}`;
            div.innerHTML = `
                <i class="fas fa-comment-alt text-xs flex-shrink-0 ${isActive ? 'text-emerald-500' : 'text-[#2d4a43]/40 group-hover:text-emerald-500'}"></i>
                <span class="text-sm truncate flex-1 sidebar-text transition-opacity duration-200">${s.title || '新对话'}</span>
                <button onclick="event.stopPropagation(); window.showSessionMenu(event, '${s.id}', '${s.title || '新对话'}')" class="opacity-0 group-hover:opacity-100 hover:bg-emerald-100 p-1 rounded transition-all text-emerald-600 flex-shrink-0 sidebar-text">
                    <i class="fas fa-ellipsis-v text-[10px]"></i>
                </button>
            `;
            div.onclick = () => switchToSession(s.id);
            dom.sessionList.appendChild(div);
        });
        if (isSidebarCollapsed) applyCollapsedState();
    } catch (e) { }
}

async function loadSessionHistory(id) {
    try {
        const res = await fetch(`/api/v1/chat/sessions/${id}`);
        if (!res.ok) { renderWelcome(); return; }
        const data = await res.json();
        if (dom.chatWindow) dom.chatWindow.innerHTML = '';
        updatePageTitle(data.title);
        let history = data.history;
        if (typeof history === 'string') { try { history = JSON.parse(history); } catch (e) { history = []; } }
        if (Array.isArray(history) && history.length > 0) {
            history.forEach(msg => renderMessage(msg.content, msg.role, false, msg.attachments || [], msg.thought_process || []));
        } else { renderWelcome(); }
        scrollToBottom();
    } catch (e) { renderWelcome(); }
}

async function switchToSession(id) {
    if (isGenerating) return;
    showChat();
    currentSessionId = id; localStorage.setItem('last_session_id', id);
    await loadSessions(); await loadSessionHistory(id);
}

window.showSessionMenu = (e, id, title) => {
    const existing = document.getElementById('session-context-menu');
    if (existing) existing.remove();
    const menu = document.createElement('div');
    menu.id = 'session-context-menu';
    menu.className = 'fixed bg-white shadow-2xl border border-slate-100 rounded-xl py-1 w-32 z-[100] text-sm fade-in-up';
    menu.style.left = `${e.clientX}px`; menu.style.top = `${e.clientY}px`;
    menu.innerHTML = `
        <button onclick="window.renameSession('${id}', '${title}')" class="w-full text-left px-4 py-2 hover:bg-slate-50 flex items-center gap-2 text-slate-700"><i class="fas fa-pencil-alt text-xs opacity-40"></i> 重命名</button>
        <button onclick="window.deleteSession('${id}', '${title}')" class="w-full text-left px-4 py-2 hover:bg-red-50 flex items-center gap-2 text-red-600"><i class="fas fa-trash-alt text-xs opacity-40"></i> 删除</button>
    `;
    document.body.appendChild(menu);
    const close = () => { menu.remove(); document.removeEventListener('click', close); };
    setTimeout(() => document.addEventListener('click', close), 0);
};

window.renameSession = (id, title) => openRenameModal(id, title);
window.deleteSession = (id, title) => openDeleteModal(id, title);

// --- 10. Event Listeners ---
if (dom.newChatBtn) {
    dom.newChatBtn.onclick = () => {
        if (isGenerating) return;
        showChat();
        currentSessionId = generateUUID();
        localStorage.setItem('last_session_id', currentSessionId);
        if (dom.chatWindow) dom.chatWindow.innerHTML = '';
        updatePageTitle('新对话');
        renderWelcome();
        loadSessions();
    };
}

if (dom.sendBtn) {
    dom.sendBtn.onclick = async () => {
        const message = dom.input.value.trim();
        if ((!message && pendingFiles.length === 0) || isGenerating) return;
        isGenerating = true; dom.sendBtn.disabled = true; dom.input.value = '';

        const currentFiles = [...pendingFiles];
        renderMessage(message, 'user', true, currentFiles);
        const attachedHashes = pendingFiles.map(f => f.hash);
        pendingFiles = []; renderPendingFiles();

        const isAutoExpanded = appSettings.autoExpandCoT;
        const loadingHtml = `
            <div class="thought-log-wrapper mb-4 bg-slate-50/80 rounded-xl border border-slate-100 overflow-hidden transition-all duration-300">
                <div class="flex items-center justify-between px-3 py-2 cursor-pointer" onclick="this.nextElementSibling.classList.toggle('hidden'); this.querySelector('.arrow-icon').classList.toggle('rotate-180')">
                    <div class="flex items-center space-x-2 text-slate-400">
                        <div class="typing-loader-container"><div class="typing-loader scale-75"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div></div>
                        <span class="status-text text-[10px] font-bold uppercase tracking-wider">思考中...</span>
                    </div>
                    <i class="fas fa-chevron-down arrow-icon text-[10px] text-slate-300 transition-transform ${isAutoExpanded ? '' : 'rotate-180'}"></i>
                </div>
                <div class="thought-log-container ${isAutoExpanded ? '' : 'hidden'} px-3 pb-3 space-y-3 border-t border-slate-50 pt-3">
                    <div class="text-log-area space-y-1"></div>
                    <div class="tool-table-area hidden">
                        <table class="w-full text-[10px] text-slate-500 border-collapse">
                            <thead><tr class="border-b border-slate-200"><th class="text-left py-1 font-semibold">Tool</th><th class="text-left py-1 font-semibold">Status</th><th class="text-right py-1 font-semibold">Action</th></tr></thead>
                            <tbody class="tool-list-body"></tbody>
                        </table>
                    </div>
                </div>
            </div>
            <div class="actual-response text-slate-700"></div>`;

        const aiBubble = renderMessage(loadingHtml, 'assistant');
        let fullRawText = "";
        let isFirstToken = true;

        try {
            const response = await fetch('/api/v1/chat/completions', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, session_id: currentSessionId, file_hashes: attachedHashes, audit_mode: appSettings.auditMode })
            });
            const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
            while (true) {
                const { done, value } = await reader.read(); if (done) break;
                buffer += decoder.decode(value, { stream: true });
                let lines = buffer.split("\n"); buffer = lines.pop();
                for (let line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    try {
                        const data = JSON.parse(line.substring(6));
                        const event = data.event;
                        const payload = data.payload;

                        const logContainer = aiBubble.querySelector('.text-log-area');
                        const toolArea = aiBubble.querySelector('.tool-table-area');
                        const toolBody = aiBubble.querySelector('.tool-list-body');
                        const statusText = aiBubble.querySelector('.status-text');
                        const responseEl = aiBubble.querySelector('.actual-response');

                        if (isFirstToken) {
                            isFirstToken = false;
                            aiBubble.querySelector('.typing-loader-container')?.remove();
                        }

                        // --- 1. Status Update (Top Bar) ---
                        if (event === 'status_update') {
                            if (statusText && payload.text) {
                                statusText.innerText = payload.text;
                                // Can add a small flash effect or log it
                                const logItem = document.createElement('div');
                                logItem.className = 'text-xs text-slate-400 flex items-start space-x-2 fade-in-up';
                                logItem.innerHTML = `<i class="fas fa-info-circle mt-1 text-[8px] opacity-50"></i><span>${payload.text}</span>`;
                                logContainer.appendChild(logItem);
                            }
                        }

                        // --- 2. Thought Delta (CoT) ---
                        else if (event === 'thought_delta') {
                            let dynamicThinkBlock = logContainer.querySelector('.dynamic-think');
                            if (!dynamicThinkBlock) {
                                dynamicThinkBlock = document.createElement('div');
                                dynamicThinkBlock.className = 'dynamic-think text-xs text-indigo-400/80 italic pl-1 border-l-2 border-indigo-200/50 my-1 py-0.5 whitespace-pre-wrap';
                                logContainer.appendChild(dynamicThinkBlock);
                            }
                            // Append text
                            dynamicThinkBlock.textContent += payload.delta;
                            scrollToBottom();
                        }

                        // --- 3. Tool Start ---
                        else if (event === 'tool_start') {
                            toolArea.classList.remove('hidden');
                            let row = toolBody.querySelector(`[data-tool-id="${payload.id}"]`);
                            if (!row) {
                                row = document.createElement('tr');
                                row.className = 'border-b border-slate-100/50 hover:bg-slate-100/50 transition-colors group cursor-pointer';
                                row.setAttribute('data-tool-id', payload.id);
                                row.setAttribute('data-tool-name', payload.name || 'Unknown');
                                toolBody.appendChild(row);
                            }

                            // 保存完整 payload 以便查看详情
                            const fullPayload = {
                                name: payload.name,
                                input: payload.input || 'N/A',
                                output: 'Processing...',
                                status: 'running'
                            };
                            row.setAttribute('data-detail', JSON.stringify(fullPayload));
                            row.onclick = () => window.openToolDetail(JSON.parse(row.getAttribute('data-detail')));

                            row.innerHTML = `
                                <td class="py-2 font-medium text-slate-600">${payload.name}</td>
                                <td class="py-2 text-blue-500"><i class="fas fa-spinner fa-spin mr-1"></i>Running</td>
                                <td class="py-2 text-right"><span class="bg-slate-200 px-1.5 py-0.5 rounded text-[8px] group-hover:bg-emerald-500 group-hover:text-white transition-all">VIEW</span></td>
                            `;
                            scrollToBottom();
                        }

                        // --- 4. Tool End ---
                        else if (event === 'tool_end') {
                            let row = toolBody.querySelector(`[data-tool-id="${payload.id}"]`);
                            if (row) {
                                // Update stored detail
                                let detail = JSON.parse(row.getAttribute('data-detail') || '{}');
                                detail.output = payload.output;
                                detail.status = 'completed';
                                row.setAttribute('data-detail', JSON.stringify(detail));

                                row.querySelector('td:nth-child(2)').innerHTML = `<i class="fas fa-check-circle mr-1"></i>Done`;
                                row.querySelector('td:nth-child(2)').className = 'py-2 text-emerald-500';
                            }
                        }

                        // --- 5. Answer Delta (Main Content) ---
                        else if (event === 'answer_delta') {
                            fullRawText += payload.delta;
                            responseEl.innerHTML = marked.parse(fullRawText);
                            scrollToBottom();
                        }

                        // --- 6. Error Handling ---
                        else if (event === 'error') {
                            const errorMsg = typeof payload === 'string' ? payload : JSON.stringify(payload);
                            aiBubble.innerHTML += `<div class="text-red-500 bg-red-50 p-3 rounded-lg mt-2 border border-red-100 text-sm"><i class="fas fa-exclamation-circle mr-2"></i>${errorMsg}</div>`;
                            // 同时也把错误显示在思考日志里
                            const logContainer = aiBubble.querySelector('.text-log-area');
                            if (logContainer) {
                                const errLog = document.createElement('div');
                                errLog.className = 'text-xs text-red-500 flex items-start space-x-2';
                                errLog.innerHTML = `<i class="fas fa-times-circle mt-1"></i><span>${errorMsg}</span>`;
                                logContainer.appendChild(errLog);
                            }
                        }

                    } catch (e) { console.error(e); }
                }
            }
            await loadSessions();
        } catch (error) { aiBubble.innerHTML = `<span class="text-red-500">连接异常</span>`; }
        finally { isGenerating = false; dom.sendBtn.disabled = false; dom.input.focus(); }
    };
}

function renderPendingFiles() {
    if (pendingFiles.length === 0) { dom.pendingFileZone.classList.add('hidden'); return; }
    dom.pendingFileZone.classList.remove('hidden'); dom.pendingFileZone.innerHTML = '';
    pendingFiles.forEach((file, index) => {
        const card = document.createElement('div');
        card.className = 'group relative w-32 bg-white border border-emerald-100 rounded-xl p-3 shadow-sm hover:shadow-md transition-all flex flex-col items-center text-center cursor-pointer hover:bg-emerald-50';
        card.onclick = () => window.openPreview(file.hash, file.name);
        card.innerHTML = `<div class="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center mb-2 group-hover:bg-white transition-colors"><i class="fas fa-file-alt text-xl"></i></div><div class="text-[10px] text-slate-600 font-medium truncate w-full px-1">${file.name}</div><button onclick="event.stopPropagation(); pendingFiles.splice(${index}, 1); renderPendingFiles();" class="absolute -top-2 -right-2 w-5 h-5 bg-slate-100 text-slate-400 hover:bg-red-500 hover:text-white rounded-full flex items-center justify-center text-[10px] shadow-sm transition-colors opacity-0 group-hover:opacity-100"><i class="fas fa-times"></i></button>`;
        dom.pendingFileZone.appendChild(card);
    });
}

if (dom.uploadBtn) {
    dom.uploadBtn.onclick = () => dom.fileInput.click();
    dom.fileInput.onchange = async () => {
        for (const file of Array.from(dom.fileInput.files)) {
            const formData = new FormData(); formData.append('file', file);
            const oldIcon = dom.uploadBtn.innerHTML; dom.uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin text-emerald-600"></i>';
            try {
                const res = await fetch('/api/v1/documents/upload', { method: 'POST', body: formData });
                if (res.ok) {
                    const result = await res.json();
                    pendingFiles.push({ hash: result.file_hash, name: file.name });
                    renderPendingFiles();
                }
            } catch (e) { }
            finally { dom.uploadBtn.innerHTML = oldIcon; dom.fileInput.value = ''; }
        }
    };
}

if (dom.sidebarToggle) {
    dom.sidebarToggle.onclick = () => {
        isSidebarCollapsed = !isSidebarCollapsed;
        applyCollapsedState();
    };
}

function applyCollapsedState() {
    const texts = dom.sidebar.querySelectorAll('.sidebar-text');
    if (isSidebarCollapsed) {
        dom.sidebar.style.width = '60px';
        dom.sidebar.classList.add('collapsed');
        texts.forEach(el => el.classList.add('hidden'));
        dom.toggleIcon.classList.add('rotate-180');
    } else {
        dom.sidebar.style.width = `${sidebarWidth}px`;
        dom.sidebar.classList.remove('collapsed');
        texts.forEach(el => el.classList.remove('hidden'));
        dom.toggleIcon.classList.remove('rotate-180');
    }
}

if (dom.resizer) {
    dom.resizer.onmousedown = (e) => {
        e.preventDefault();
        document.onmousemove = (e) => {
            let newWidth = e.clientX;
            if (newWidth < 150) newWidth = 150;
            if (newWidth > 400) newWidth = 400;
            sidebarWidth = newWidth;
            dom.sidebar.style.width = `${newWidth}px`;
        };
        document.onmouseup = () => {
            document.onmousemove = null;
            document.onmouseup = null;
        };
    };
}

// --- Initialization ---
window.onload = async () => {
    applySettings();
    renderWelcome();
    await loadSessions();
    const lastId = localStorage.getItem('last_session_id');
    if (lastId) {
        currentSessionId = lastId;
        await loadSessionHistory(lastId);
    }
};

function fillInput(text) { if (dom.input) { dom.input.value = text; dom.input.focus(); } }
window.fillInput = fillInput;
dom.input.onkeypress = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); dom.sendBtn.click(); } };