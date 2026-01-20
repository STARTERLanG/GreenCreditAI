// --- 1. Utils & Helpers ---
function getFileCardHtml(name) {
    return `
        <div class="flex items-center bg-white/80 border border-emerald-100 rounded-lg p-2 mb-2 shadow-sm w-fit max-w-[200px]">
            <div class="w-8 h-8 bg-emerald-50 text-emerald-600 rounded flex items-center justify-center mr-3 flex-shrink-0">
                <i class="fas fa-file-alt text-lg"></i>
            </div>
            <div class="text-[11px] text-slate-700 font-medium truncate">${name}</div>
        </div>
    `;
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function scrollToBottom() {
    if (dom.chatWindow) {
        dom.chatWindow.scrollTop = dom.chatWindow.scrollHeight;
    }
}

function updatePageTitle(title) {
    document.title = `绿色信贷智能助手 - ${title || '新对话'}`;
}

// --- 2. State & Config ---
let currentSessionId = localStorage.getItem('last_session_id') || generateUUID();
let isGenerating = false;
let isSidebarCollapsed = false; 
let sidebarWidth = 250; 
let pendingRenameId = null;
let pendingDeleteId = null;

// 附件状态
let pendingFiles = []; // [{hash, name}]

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
    // Modal
    renameModal: document.getElementById('rename-modal'),
    modalContent: document.getElementById('modal-content'),
    renameInput: document.getElementById('rename-input'),
    cancelRenameBtn: document.getElementById('cancel-rename-btn'),
    confirmRenameBtn: document.getElementById('confirm-rename-btn'),
    // Delete Modal
    deleteModal: document.getElementById('delete-modal'),
    deleteModalContent: document.getElementById('delete-modal-content'),
    deleteModalTitle: document.getElementById('delete-modal-title'),
    cancelDeleteBtn: document.getElementById('cancel-delete-btn'),
    confirmDeleteBtn: document.getElementById('confirm-delete-btn'),
    // Pending File
    pendingFileZone: document.getElementById('pending-file-zone')
};

// --- 4. Sidebar & Resize Logic ---
if (dom.resizer && dom.sidebar) {
    let isResizing = false;
    dom.resizer.addEventListener('mousedown', (e) => {
        console.log("Resizer: Mouse Down");
        isResizing = true; e.preventDefault();
        dom.resizer.classList.add('resizing');
        document.body.style.cursor = 'col-resize';
        dom.sidebar.style.transition = 'none';
    });
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        let newWidth = e.clientX;
        if (newWidth < 60) newWidth = 60;
        if (newWidth > 500) newWidth = 500;
        sidebarWidth = newWidth;
        dom.sidebar.style.width = `${newWidth}px`;
        dom.sidebar.style.flexBasis = `${newWidth}px`;
        if (newWidth < 100 && !isSidebarCollapsed) collapseSidebar();
        else if (newWidth >= 100 && isSidebarCollapsed) expandSidebar();
    });
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            console.log("Resizer: Mouse Up");
            isResizing = false; dom.resizer.classList.remove('resizing');
            document.body.style.cursor = 'default';
            dom.sidebar.style.transition = 'width 0.3s ease-in-out';
        }
    });
}

function collapseSidebar() {
    isSidebarCollapsed = true;
    dom.sidebar.style.width = '80px'; dom.sidebar.style.flexBasis = '80px';
    dom.toggleIcon.classList.add('rotate-180');
    document.querySelectorAll('.sidebar-text').forEach(el => el.classList.add('hidden'));
    if (dom.searchBtn) dom.searchBtn.classList.add('hidden');
    dom.newChatBtn.classList.remove('px-4', 'space-x-2');
    dom.newChatBtn.classList.add('justify-center', 'px-0');
}

function expandSidebar() {
    isSidebarCollapsed = false;
    const targetWidth = sidebarWidth < 150 ? 250 : sidebarWidth;
    dom.sidebar.style.width = `${targetWidth}px`; dom.sidebar.style.flexBasis = `${targetWidth}px`;
    dom.toggleIcon.classList.remove('rotate-180');
    document.querySelectorAll('.sidebar-text').forEach(el => el.classList.remove('hidden'));
    if (dom.searchBtn) dom.searchBtn.classList.remove('hidden');
    dom.newChatBtn.classList.add('px-4', 'space-x-2');
    dom.newChatBtn.classList.remove('justify-center', 'px-0');
}

if (dom.sidebarToggle) dom.sidebarToggle.onclick = () => isSidebarCollapsed ? expandSidebar() : collapseSidebar();

// --- 5. Modal Logic ---
function openRenameModal(id, currentTitle) {
    pendingRenameId = id; dom.renameInput.value = currentTitle;
    dom.renameModal.classList.remove('hidden');
    setTimeout(() => { dom.renameModal.classList.remove('opacity-0'); dom.modalContent.classList.replace('scale-95', 'scale-100'); }, 10);
    dom.renameInput.focus();
}
function closeRenameModal() {
    dom.renameModal.classList.add('opacity-0'); dom.modalContent.classList.replace('scale-100', 'scale-95');
    setTimeout(() => { dom.renameModal.classList.add('hidden'); pendingRenameId = null; }, 200);
}
function openDeleteModal(id, title) {
    pendingDeleteId = id;
    if (dom.deleteModalTitle) dom.deleteModalTitle.innerText = `删除会话: ${title || '未命名'}`;
    dom.deleteModal.classList.remove('hidden');
    setTimeout(() => { dom.deleteModal.classList.remove('opacity-0'); dom.deleteModalContent.classList.replace('scale-95', 'scale-100'); }, 10);
}
function closeDeleteModal() {
    dom.deleteModal.classList.add('opacity-0'); dom.deleteModalContent.classList.replace('scale-100', 'scale-95');
    setTimeout(() => { dom.deleteModal.classList.add('hidden'); pendingDeleteId = null; }, 200);
}
if (dom.cancelRenameBtn) dom.cancelRenameBtn.onclick = closeRenameModal;
if (dom.cancelDeleteBtn) dom.cancelDeleteBtn.onclick = closeDeleteModal;
if (dom.confirmDeleteBtn) {
    dom.confirmDeleteBtn.onclick = async () => {
        if (!pendingDeleteId) return;
        try {
            await fetch(`/api/v1/chat/sessions/${pendingDeleteId}`, { method: 'DELETE' });
            if (pendingDeleteId === currentSessionId) dom.newChatBtn.click(); else await loadSessions();
            closeDeleteModal();
        } catch (e) { alert("删除失败"); }
    };
}
if (dom.confirmRenameBtn) {
    dom.confirmRenameBtn.onclick = async () => {
        const newTitle = dom.renameInput.value.trim();
        if (!newTitle || !pendingRenameId) return;
        try {
            await fetch(`/api/v1/chat/sessions/${pendingRenameId}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: newTitle }) });
            await loadSessions(); if (pendingRenameId === currentSessionId) updatePageTitle(newTitle);
            closeRenameModal();
        } catch (e) { alert("重命名失败"); }
    };
}

// --- 6. Render Logic ---
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
function fillInput(text) { if (dom.input) { dom.input.value = text; dom.input.focus(); } }
window.fillInput = fillInput;

function renderMessage(content, role, animate = true, isHtml = false) {
    if (!dom.chatWindow) return;
    const welcome = dom.chatWindow.querySelector('.welcome-screen');
    if (welcome) welcome.remove();

    const wrapper = document.createElement('div');
    wrapper.className = `msg-wrapper mb-8 ${animate ? 'fade-in-up' : ''}`;
    const isUser = role === 'user';
    const avatarImg = isUser ? '/static/img/user-avatar.svg' : '/static/img/ai-avatar.svg';
    
    // ... (actionsHtml 保持不变)
    const actionsHtml = isUser ? `
        <div class="msg-actions justify-end mr-1">
            <button class="action-btn copy-btn" title="复制"><i class="fas fa-copy"></i></button>
            <button class="action-btn" title="编辑"><i class="fas fa-pencil-alt text-xs"></i></button>
        </div>` : `
        <div class="msg-actions ml-1">
            <button class="action-btn copy-btn" title="复制"><i class="fas fa-copy"></i></button>
            <button class="action-btn" title="重新生成"><i class="fas fa-sync-alt"></i></button>
            <button class="action-btn" title="赞"><i class="far fa-thumbs-up"></i></button>
            <button class="action-btn" title="踩"><i class="far fa-thumbs-down"></i></button>
        </div>`;

    const avatarHtml = `<img src="${avatarImg}" class="avatar ${isUser ? 'order-2 ml-4' : 'order-1 mr-4'}" alt="${role}">`;
    
    // 内容处理：支持 HTML 注入和附件标记解析
    let htmlContent = '';
    if (isUser) {
        // 识别 [附件: file1, file2] 格式
        const attachmentRegex = /^\[附件:\s*(.*?)\]\n?/;
        const match = content.match(attachmentRegex);
        
        if (match) {
            const fileNames = match[1].split(',').map(n => n.trim());
            const restOfContent = content.replace(attachmentRegex, '').trim();
            
            let cardsHtml = `<div class="file-cards-list mb-2 flex flex-wrap gap-2">`;
            fileNames.forEach(name => {
                cardsHtml += getFileCardHtml(name);
            });
            cardsHtml += `</div>`;
            
            htmlContent = `<div>${cardsHtml}${restOfContent ? `<div class="whitespace-pre-wrap">${restOfContent}</div>` : ''}</div>`;
        } else if (isHtml) {
            htmlContent = `<div>${content}</div>`;
        } else {
            htmlContent = `<div class="whitespace-pre-wrap">${content}</div>`;
        }
    } else {
        htmlContent = `<div class="markdown-body">${marked.parse(content)}</div>`;
    }

    const bubbleClass = isUser ? 'bg-gray-100 text-gray-800 rounded-[20px] rounded-tr-sm px-5 py-3' : 'text-gray-800 pt-1 w-full';
    wrapper.innerHTML = `
        <div class="msg-content-container flex w-full ${isUser ? 'justify-end' : 'justify-start'}">
            ${avatarHtml}
            <div class="flex flex-col ${isUser ? 'order-1 items-end' : 'order-2 items-start'} flex-1 min-w-0 max-w-[85%]">
                <div class="${bubbleClass} msg-bubble leading-relaxed">${htmlContent}</div>
                <div class="mt-1 ${isUser ? 'mr-1' : 'ml-1'}">${actionsHtml}</div>
            </div>
        </div>
    `;
    const copyBtn = wrapper.querySelector('.copy-btn');
    if (copyBtn) copyBtn.onclick = () => {
        navigator.clipboard.writeText(content).then(() => {
            const icon = copyBtn.querySelector('i'); const old = icon.className;
            icon.className = 'fas fa-check text-emerald-500 icon-pop';
            setTimeout(() => icon.className = old, 1500);
        });
    };
    
    const likeBtn = wrapper.querySelector('.fa-thumbs-up')?.parentElement;
    const dislikeBtn = wrapper.querySelector('.fa-thumbs-down')?.parentElement;
    if (likeBtn) likeBtn.onclick = () => {
        const icon = likeBtn.querySelector('i'); const isActive = likeBtn.classList.toggle('active-like');
        icon.className = isActive ? 'fas fa-thumbs-up icon-pop' : 'far fa-thumbs-up';
        if (dislikeBtn) { dislikeBtn.classList.remove('active-dislike'); dislikeBtn.querySelector('i').className = 'far fa-thumbs-down'; }
    };
    if (dislikeBtn) dislikeBtn.onclick = () => {
        const icon = dislikeBtn.querySelector('i'); const isActive = dislikeBtn.classList.toggle('active-dislike');
        icon.className = isActive ? 'fas fa-thumbs-down icon-pop' : 'far fa-thumbs-down';
        if (likeBtn) { likeBtn.classList.remove('active-like'); likeBtn.querySelector('i').className = 'far fa-thumbs-up'; }
    };

    dom.chatWindow.appendChild(wrapper); scrollToBottom();
    return isUser ? null : wrapper.querySelector('.markdown-body');
}

// --- 7. API Interactions ---
async function loadSessions() {
    try {
        const res = await fetch('/api/v1/chat/sessions');
        const sessions = await res.json();
        if (!dom.sessionList) return; dom.sessionList.innerHTML = '';
        sessions.forEach(s => {
            const isActive = s.id === currentSessionId; const div = document.createElement('div');
            div.className = `group px-3 py-2.5 rounded-xl cursor-pointer flex items-center space-x-3 mb-1 transition-all duration-200 relative ${isActive ? 'bg-white shadow-sm text-emerald-800 font-bold border border-[#d1e2da]' : 'text-[#2d4a43]/70 hover:bg-white/40 hover:text-[#2d4a43]'}`;
            const textClass = isSidebarCollapsed ? 'hidden sidebar-text' : 'sidebar-text';
            div.innerHTML = `
                <i class="fas fa-comment-alt text-xs ${isActive ? 'text-emerald-500' : 'text-[#2d4a43]/40 group-hover:text-emerald-500'} flex-shrink-0"></i>
                <span class="text-sm truncate flex-1 ${textClass}">${s.title || '新对话'}</span>
                <button class="menu-btn absolute right-2 opacity-0 group-hover:opacity-100 p-1 hover:bg-black/5 rounded text-xs transition-opacity ${isSidebarCollapsed ? 'hidden' : ''}" onclick="event.stopPropagation(); window.showSessionMenu(event, '${s.id}', '${s.title}')">
                    <i class="fas fa-ellipsis-h text-slate-400"></i>
                </button>
            `;
            div.onclick = () => switchToSession(s.id); dom.sessionList.appendChild(div);
        });
    } catch(e) {}
}

async function loadSessionHistory(id) {
    try {
        const res = await fetch(`/api/v1/chat/sessions/${id}`); if (!res.ok) { renderWelcome(); return; }
        const data = await res.json(); if (dom.chatWindow) dom.chatWindow.innerHTML = ''; 
        updatePageTitle(data.title);
        const history = Array.isArray(data.history) ? data.history : [];
        if (history.length > 0) history.forEach(msg => renderMessage(msg.content, msg.role, false)); else renderWelcome();
        scrollToBottom();
    } catch (e) { renderWelcome(); }
}

async function switchToSession(id) {
    if(isGenerating) return; currentSessionId = id; localStorage.setItem('last_session_id', id);
    await loadSessions(); await loadSessionHistory(id);
}

// --- 8. Session Menu & Context ---
window.showSessionMenu = (e, id, title) => {
    const existing = document.getElementById('session-context-menu'); if (existing) existing.remove();
    const menu = document.createElement('div'); menu.id = 'session-context-menu';
    menu.className = 'fixed bg-white shadow-2xl border border-slate-100 rounded-xl py-1 w-32 z-[100] text-sm fade-in-up';
    menu.style.left = `${e.clientX}px`; menu.style.top = `${e.clientY}px`;
    menu.innerHTML = `
        <button onclick="window.renameSession('${id}', '${title}')" class="w-full text-left px-4 py-2 hover:bg-slate-50 flex items-center gap-2 text-slate-700"><i class="fas fa-pencil-alt text-xs opacity-40"></i> 重命名</button>
        <button onclick="window.deleteSession('${id}', '${title}')" class="w-full text-left px-4 py-2 hover:bg-red-50 flex items-center gap-2 text-red-600"><i class="fas fa-trash-alt text-xs opacity-40"></i> 删除</button>
    `;
    document.body.appendChild(menu);
    const close = () => { menu.remove(); document.removeEventListener('click', close); }; setTimeout(() => document.addEventListener('click', close), 0);
};
window.renameSession = (id, title) => openRenameModal(id, title);
window.deleteSession = (id, title) => openDeleteModal(id, title);

// --- 9. Pending File Rendering ---
function renderPendingFiles() {
    if (pendingFiles.length === 0) {
        dom.pendingFileZone.classList.add('hidden');
        return;
    }
    dom.pendingFileZone.classList.remove('hidden');
    dom.pendingFileZone.innerHTML = '';
    pendingFiles.forEach((file, index) => {
        const card = document.createElement('div');
        card.className = 'group relative w-32 bg-white border border-emerald-100 rounded-xl p-3 shadow-sm hover:shadow-md transition-all flex flex-col items-center text-center';
        card.innerHTML = `
            <div class="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center mb-2">
                <i class="fas fa-file-alt text-xl"></i>
            </div>
            <div class="text-[10px] text-slate-600 font-medium truncate w-full px-1">${file.name}</div>
            <button onclick="removePendingFile(${index})" class="absolute -top-2 -right-2 w-5 h-5 bg-slate-100 text-slate-400 hover:bg-red-500 hover:text-white rounded-full flex items-center justify-center text-[10px] shadow-sm transition-colors opacity-0 group-hover:opacity-100">
                <i class="fas fa-times"></i>
            </button>
        `;
        dom.pendingFileZone.appendChild(card);
    });
}

window.removePendingFile = (index) => {
    pendingFiles.splice(index, 1);
    renderPendingFiles();
};

// --- 10. Event Listeners ---
if (dom.newChatBtn) {
    dom.newChatBtn.onclick = () => {
        if(isGenerating) return;
        currentSessionId = generateUUID(); localStorage.setItem('last_session_id', currentSessionId);
        dom.chatWindow.innerHTML = ''; updatePageTitle('新对话'); renderWelcome(); loadSessions();
    };
}

if (dom.sendBtn) {
    dom.sendBtn.onclick = async () => {
        const message = dom.input.value.trim();
        if ((!message && pendingFiles.length === 0) || isGenerating) return;
        isGenerating = true; dom.sendBtn.disabled = true; dom.input.value = '';
        
        // 组装带标记的消息 (供持久化和后续解析)
        let finalMsg = message;
        if (pendingFiles.length > 0) {
            const fileListStr = pendingFiles.map(f => f.name).join(', ');
            finalMsg = `[附件: ${fileListStr}]\n${message}`;
        }
        
        // 渲染消息 (renderMessage 内部会解析这个标记并显示卡片)
        renderMessage(finalMsg, 'user');
        
        // 提取哈希用于发送
        const attachedHashes = pendingFiles.map(f => f.hash);
        pendingFiles = []; renderPendingFiles();

        const loadingHtml = `<div class="typing-loader"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;
        const aiContentDiv = renderMessage(loadingHtml, 'assistant');
        let fullText = "", isFirstToken = true;
        
        try {
            // 这里我们暂时只传第一个文件哈希，后端目前只支持一个。后续可扩展为 file_hashes 数组。
            const response = await fetch('/api/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message, 
                    session_id: currentSessionId, 
                    file_hashes: attachedHashes 
                })
            });
            const reader = response.body.getReader(); const decoder = new TextDecoder("utf-8"); let buffer = "";
                        while (true) {
                            const { done, value } = await reader.read(); if (done) break;
                            buffer += decoder.decode(value, { stream: true }); let lines = buffer.split("\n"); buffer = lines.pop();
                            for (let line of lines) {
                                line = line.trim(); if (!line || !line.startsWith("data: ")) continue;
                                try {
                                    const data = JSON.parse(line.substring(6));
                                    
                                                            // 处理思考状态
                                                            if (data.event === 'think') {
                                                                const statusEl = aiContentDiv.querySelector('.typing-status');
                                                                if (statusEl) {
                                                                    statusEl.innerText = data.payload;
                                                                } else {
                                                                    aiContentDiv.innerHTML = `
                                                                        <div class="flex items-center space-x-3 text-slate-500 py-2">
                                                                            <div class="typing-loader">
                                                                                <div class="typing-dot"></div>
                                                                                <div class="typing-dot"></div>
                                                                                <div class="typing-dot"></div>
                                                                            </div>
                                                                            <div class="typing-status text-xs font-semibold tracking-tight text-slate-600">${data.payload}</div>
                                                                        </div>
                                                                    `;
                                                                }
                                                            }
                                                                        // 处理正式回复
                                    if (data.event === 'token' && data.payload) {
                                        if (isFirstToken) { 
                                            aiContentDiv.innerHTML = ""; 
                                            isFirstToken = false; 
                                        }
                                        fullText += data.payload;
                                        aiContentDiv.innerHTML = marked.parse(fullText);
                                        scrollToBottom();
                                    }
                                } catch (e) {}
                            }
                        }
            
            await loadSessions();
            const res = await fetch(`/api/v1/chat/sessions/${currentSessionId}`); if (res.ok) { const d = await res.json(); updatePageTitle(d.title); }
        } catch (error) { aiContentDiv.innerHTML = `<span class="text-red-500">连接异常</span>`; }
        finally { isGenerating = false; dom.sendBtn.disabled = false; dom.input.focus(); }
    };
}

if (dom.uploadBtn) {
    dom.uploadBtn.onclick = () => dom.fileInput.click();
    dom.fileInput.onchange = async () => {
        if (dom.fileInput.files.length > 0) {
            const files = Array.from(dom.fileInput.files);
            for (const file of files) {
                const formData = new FormData(); formData.append('file', file);
                const oldIcon = dom.uploadBtn.innerHTML;
                dom.uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin text-emerald-600"></i>';
                dom.uploadBtn.disabled = true;
                try {
                    const res = await fetch('/api/v1/documents/upload', { method: 'POST', body: formData });
                    if (res.ok) {
                        const result = await res.json();
                        pendingFiles.push({ hash: result.file_hash, name: file.name });
                        renderPendingFiles();
                    }
                } catch (e) {}
                finally {
                    dom.uploadBtn.innerHTML = oldIcon; dom.uploadBtn.disabled = false;
                }
            }
            dom.fileInput.value = '';
        }
    };
}

dom.input.onkeypress = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); dom.sendBtn.click(); } };

// --- 11. Init ---
window.onload = async () => {
    updatePageTitle('新对话'); renderWelcome(); await loadSessions();
    const lastId = localStorage.getItem('last_session_id');
    if (lastId) { currentSessionId = lastId; await loadSessionHistory(lastId); await loadSessions(); }
};