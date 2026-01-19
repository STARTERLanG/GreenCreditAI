// --- Utils ---
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

// --- State ---
let currentSessionId = localStorage.getItem('last_session_id') || generateUUID();
let isGenerating = false;
let isSidebarCollapsed = false; 
let sidebarWidth = 250; // 默认宽度

// --- DOM Elements ---
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
    resizer: document.getElementById('sidebar-resizer'), // 新增
    // Modal Elements
    renameModal: document.getElementById('rename-modal'),
    modalContent: document.getElementById('modal-content'),
    renameInput: document.getElementById('rename-input'),
    cancelRenameBtn: document.getElementById('cancel-rename-btn'),
    confirmRenameBtn: document.getElementById('confirm-rename-btn')
};

// --- Modal Logic ---
let pendingRenameId = null;

function openRenameModal(id, currentTitle) {
    pendingRenameId = id;
    dom.renameInput.value = currentTitle;
    
    dom.renameModal.classList.remove('hidden');
    // 简单的淡入动画
    setTimeout(() => {
        dom.renameModal.classList.remove('opacity-0');
        dom.modalContent.classList.remove('scale-95');
        dom.modalContent.classList.add('scale-100');
    }, 10);
    
    dom.renameInput.focus();
}

function closeRenameModal() {
    dom.renameModal.classList.add('opacity-0');
    dom.modalContent.classList.remove('scale-100');
    dom.modalContent.classList.add('scale-95');
    
    setTimeout(() => {
        dom.renameModal.classList.add('hidden');
        pendingRenameId = null;
    }, 200);
}

// 绑定 Modal 事件
if (dom.cancelRenameBtn) dom.cancelRenameBtn.onclick = closeRenameModal;

if (dom.confirmRenameBtn) {
    dom.confirmRenameBtn.onclick = async () => {
        const newTitle = dom.renameInput.value.trim();
        if (!newTitle || !pendingRenameId) return;
        
        const oldText = dom.confirmRenameBtn.innerText;
        dom.confirmRenameBtn.innerText = "Saving...";
        dom.confirmRenameBtn.disabled = true;

        try {
            await fetch(`/api/v1/chat/sessions/${pendingRenameId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: newTitle })
            });
            await loadSessions(); 
            if (pendingRenameId === currentSessionId) updatePageTitle(newTitle);
            closeRenameModal();
        } catch (e) { 
            alert("重命名失败"); 
        } finally {
            dom.confirmRenameBtn.innerText = oldText;
            dom.confirmRenameBtn.disabled = false;
        }
    };
}

// 支持回车提交
if (dom.renameInput) {
    dom.renameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') dom.confirmRenameBtn.click();
    });
}

// 点击遮罩关闭
if (dom.renameModal) {
    dom.renameModal.addEventListener('click', (e) => {
        if (e.target === dom.renameModal) closeRenameModal();
    });
}

// 修改原有的 renameSession 调用
function renameSession(id, oldTitle) {
    openRenameModal(id, oldTitle);
}

// --- Sidebar Logic ---

// Resizer Logic
if (dom.resizer && dom.sidebar) {
    let isResizing = false;

    dom.resizer.addEventListener('mousedown', (e) => {
        console.log("Resizer: Mouse Down"); // DEBUG
        isResizing = true;
        e.preventDefault(); 
        dom.resizer.classList.add('resizing');
        document.body.style.cursor = 'col-resize';
        dom.sidebar.style.transition = 'none'; // 禁用动画
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        let newWidth = e.clientX;
        // console.log("Resizing:", newWidth); // DEBUG (可选，量大慎开)

        if (newWidth < 60) newWidth = 60;
        if (newWidth > 500) newWidth = 500;
        
        sidebarWidth = newWidth;
        dom.sidebar.style.width = `${newWidth}px`;
        // Flex 布局下有时需要设置 flex-basis
        dom.sidebar.style.flexBasis = `${newWidth}px`;
        
        if (newWidth < 100 && !isSidebarCollapsed) {
            collapseSidebar();
        } else if (newWidth >= 100 && isSidebarCollapsed) {
            expandSidebar();
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            console.log("Resizer: Mouse Up"); // DEBUG
            isResizing = false;
            dom.resizer.classList.remove('resizing');
            document.body.style.cursor = 'default';
            // 恢复动画
            dom.sidebar.style.transition = 'width 0.3s ease-in-out';
        }
    });
}

if (dom.sidebarToggle) {
    dom.sidebarToggle.onclick = () => {
        if (isSidebarCollapsed) {
            expandSidebar();
        } else {
            collapseSidebar();
        }
    };
}

// 确保这两个函数被正确提升或定义
function collapseSidebar() {
    isSidebarCollapsed = true;
    
    // 强制覆盖拖拽留下的内联 width
    dom.sidebar.style.width = '80px'; 
    dom.sidebar.style.flexBasis = '80px';
    
    dom.toggleIcon.classList.add('rotate-180');
    
    document.querySelectorAll('.sidebar-text').forEach(el => el.classList.add('hidden'));
    if (dom.searchBtn) dom.searchBtn.classList.add('hidden');
    
    dom.newChatBtn.classList.remove('px-4', 'space-x-2');
    dom.newChatBtn.classList.add('justify-center', 'px-0');
}

function expandSidebar() {
    isSidebarCollapsed = false;
    
    // 恢复用户拖拽的宽度 (最小 150)
    const targetWidth = sidebarWidth < 150 ? 250 : sidebarWidth;
    
    dom.sidebar.style.width = `${targetWidth}px`;
    dom.sidebar.style.flexBasis = `${targetWidth}px`;
    
    dom.toggleIcon.classList.remove('rotate-180');
    
    document.querySelectorAll('.sidebar-text').forEach(el => el.classList.remove('hidden'));
    if (dom.searchBtn) dom.searchBtn.classList.remove('hidden');
    
    dom.newChatBtn.classList.add('px-4', 'space-x-2');
    dom.newChatBtn.classList.remove('justify-center', 'px-0');
}

if (dom.searchBtn) {
    dom.searchBtn.onclick = () => {
        alert("搜索功能开发中...");
    };
}

// --- Render Logic ---
function renderWelcome() {
    if (!dom.chatWindow) return;
    dom.chatWindow.innerHTML = `
        <div class="welcome-screen flex flex-col items-center justify-center min-h-[70vh] fade-in-up px-4">
            <div class="text-center space-y-4 mb-12">
                <div class="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-500 to-teal-600 pb-2">
                    Hello, Banker
                </div>
                <h2 class="text-xl md:text-2xl text-slate-400 font-light">How can I help you today?</h2>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl mt-4 px-10">
                <div onclick="fillInput('光伏行业的最新准入标准是什么？')" class="group bg-white p-3 rounded-xl hover:bg-emerald-50 cursor-pointer transition-all duration-300 border border-slate-100 hover:border-emerald-200 shadow-sm flex items-center space-x-3">
                    <div class="bg-emerald-50 p-2 rounded-lg text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors flex-shrink-0">
                        <i class="fas fa-search-dollar text-xs"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-xs font-semibold text-slate-700 truncate">查询政策</div>
                        <div class="text-[10px] text-slate-400 truncate">"光伏行业的最新准入标准是什么？"</div>
                    </div>
                </div>
                
                <div onclick="fillInput('分析这份财报的环境风险')" class="group bg-white p-3 rounded-xl hover:bg-emerald-50 cursor-pointer transition-all duration-300 border border-slate-100 hover:border-emerald-200 shadow-sm flex items-center space-x-3">
                    <div class="bg-blue-50 p-2 rounded-lg text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors flex-shrink-0">
                        <i class="fas fa-file-contract text-xs"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-xs font-semibold text-slate-700 truncate">分析财报</div>
                        <div class="text-[10px] text-slate-400 truncate">"上传 PDF 并提取财务指标"</div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function fillInput(text) {
    if (dom.input) {
        dom.input.value = text;
        dom.input.focus();
    }
}
window.fillInput = fillInput;

function renderMessage(content, role, animate = true) {
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
            <button class="action-btn" title="编辑"><i class="fas fa-pencil-alt"></i></button>
        </div>` 
    : `
        <div class="msg-actions ml-1">
            <button class="action-btn copy-btn" title="复制"><i class="fas fa-copy"></i></button>
            <button class="action-btn" title="重新生成"><i class="fas fa-sync-alt"></i></button>
            <button class="action-btn" title="赞"><i class="far fa-thumbs-up"></i></button>
            <button class="action-btn" title="踩"><i class="far fa-thumbs-down"></i></button>
        </div>`;

    const avatarHtml = `<img src="${avatarImg}" class="avatar" alt="${role}">`;

    let htmlContent = '';
    if (isUser) {
        htmlContent = `<div class="whitespace-pre-wrap">${content}</div>`;
    } else {
        htmlContent = `<div class="markdown-body">${marked.parse(content)}</div>`;
    }

    const bubbleClass = isUser 
        ? 'bg-gray-100 text-gray-800 rounded-[20px] rounded-tr-sm px-5 py-3'
        : 'text-gray-800 pt-1 w-full'; 

    // 结构：Wrapper -> Container(Centered) 
    // 使用 order 属性控制左右顺序，这是最稳健的方式
    wrapper.innerHTML = `
        <div class="msg-content-container flex w-full ${isUser ? 'justify-end' : 'justify-start'}">
            
            <!-- Avatar: AI=Order-1 (Left), User=Order-2 (Right) -->
            <img src="${avatarImg}" class="avatar ${isUser ? 'order-2 ml-4' : 'order-1 mr-4'}" alt="${role}">
            
            <!-- Content Column: AI=Order-2, User=Order-1 -->
            <div class="flex flex-col ${isUser ? 'order-1 items-end' : 'order-2 items-start'} flex-1 min-w-0 max-w-[85%]">
                
                <!-- 1. Bubble -->
                <div class="${bubbleClass} msg-bubble leading-relaxed">
                    ${htmlContent}
                </div>
                
                <!-- 2. Actions (Always Below Bubble) -->
                <div class="mt-1 ${isUser ? 'mr-1' : 'ml-1'}">
                    ${actionsHtml}
                </div>
            </div>
        </div>
    `;

    const copyBtn = wrapper.querySelector('.copy-btn');
    if (copyBtn) {
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(content).then(() => {
                const icon = copyBtn.querySelector('i');
                icon.className = 'fas fa-check text-emerald-500 icon-pop';
                setTimeout(() => icon.className = 'fas fa-copy', 1500);
            });
        };
    }

    dom.chatWindow.appendChild(wrapper);
    scrollToBottom();
    
    return role === 'assistant' ? wrapper.querySelector('.markdown-body') : null;
}

// --- API Interactions ---
async function loadSessions() {
    try {
        const res = await fetch('/api/v1/chat/sessions');
        const sessions = await res.json();
        if (dom.sessionList) {
            dom.sessionList.innerHTML = '';
            sessions.forEach(s => {
                const isActive = s.id === currentSessionId;
                const div = document.createElement('div');
                div.className = `group px-3 py-2.5 rounded-xl cursor-pointer flex items-center space-x-3 mb-1 transition-all duration-200 relative ${isActive ? 'bg-white shadow-sm text-emerald-800 font-bold border border-[#d1e2da]' : 'text-[#2d4a43]/70 hover:bg-white/40 hover:text-[#2d4a43]'}`;
                
                const textClass = isSidebarCollapsed ? 'hidden sidebar-text' : 'sidebar-text';
                
                div.innerHTML = `
                    <i class="fas fa-comment-alt text-xs ${isActive ? 'text-emerald-500' : 'text-[#2d4a43]/40 group-hover:text-emerald-500'} flex-shrink-0"></i>
                    <span class="text-sm truncate flex-1 ${textClass}">${s.title || '新对话'}</span>
                    
                    <!-- Menu Button (Hover Only) -->
                    <button class="menu-btn absolute right-2 opacity-0 group-hover:opacity-100 p-1 hover:bg-black/10 rounded text-xs transition-opacity ${isSidebarCollapsed ? 'hidden' : ''}" onclick="showSessionMenu(event, '${s.id}', '${s.title}')">
                        <i class="fas fa-ellipsis-h text-slate-400"></i>
                    </button>
                `;
                div.onclick = (e) => {
                    // 如果点击的是 menu-btn，不要切换会话
                    if (e.target.closest('.menu-btn')) return;
                    switchToSession(s.id);
                };
                dom.sessionList.appendChild(div);
            });
        }
    } catch(e) { console.error(e); }
}

// --- Session Menu Logic ---
let activeMenuSessionId = null;

function showSessionMenu(e, id, currentTitle) {
    e.stopPropagation();
    activeMenuSessionId = id;
    
    // 移除已存在的菜单
    removeMenu();

    const menu = document.createElement('div');
    menu.id = 'session-context-menu';
    menu.className = 'fixed bg-white shadow-xl border border-slate-100 rounded-lg py-1 w-32 z-50 flex flex-col text-sm';
    menu.style.left = `${e.clientX + 10}px`;
    menu.style.top = `${e.clientY}px`;
    
    menu.innerHTML = `
        <button onclick="renameSession('${id}', '${currentTitle}')" class="text-left px-4 py-2 hover:bg-slate-50 text-slate-700 flex items-center gap-2">
            <i class="fas fa-pencil-alt text-xs opacity-50"></i> 重命名
        </button>
        <button onclick="deleteSession('${id}')" class="text-left px-4 py-2 hover:bg-red-50 text-red-600 flex items-center gap-2">
            <i class="fas fa-trash-alt text-xs opacity-50"></i> 删除
        </button>
    `;
    
    document.body.appendChild(menu);
    
    // 点击其他地方关闭菜单
    const closeMenu = () => {
        removeMenu();
        document.removeEventListener('click', closeMenu);
    };
    // 延迟绑定，防止当前点击立即触发关闭
    setTimeout(() => document.addEventListener('click', closeMenu), 0);
}

function removeMenu() {
    const existing = document.getElementById('session-context-menu');
    if (existing) existing.remove();
}

// renameSession 已被重写为调用 openRenameModal，此处旧代码移除

async function deleteSession(id) {
    if (confirm("确定要删除这个会话吗？此操作无法撤销。")) {
        try {
            await fetch(`/api/v1/chat/sessions/${id}`, { method: 'DELETE' });
            
            // 如果删除的是当前会话，新建一个
            if (id === currentSessionId) {
                dom.newChatBtn.click();
            } else {
                loadSessions(); // 仅刷新列表
            }
        } catch (e) { alert("删除失败"); }
    }
}

// 暴露给全局以便 onclick 调用
window.showSessionMenu = showSessionMenu;
window.renameSession = renameSession;
window.deleteSession = deleteSession;

async function loadSessionHistory(id) {
    try {
        console.log("Loading history for:", id);
        const res = await fetch(`/api/v1/chat/sessions/${id}`);
        if (!res.ok) {
            console.error("Session not found");
            renderWelcome();
            return;
        }
        const data = await res.json();
        console.log("History data:", data);
        
        if (dom.chatWindow) dom.chatWindow.innerHTML = ''; 
        updatePageTitle(data.title);
        
        const history = Array.isArray(data.history) ? data.history : [];
        
        if (history.length > 0) {
            history.forEach(msg => renderMessage(msg.content, msg.role, false));
            scrollToBottom();
        } else {
            renderWelcome();
        }
    } catch (e) {
        console.error("Failed to load history:", e);
        renderWelcome(); 
    }
}

async function switchToSession(id) {
    if(isGenerating) return;
    currentSessionId = id;
    localStorage.setItem('last_session_id', id);
    await loadSessions(); 
    await loadSessionHistory(id);
}

// --- Event Listeners ---
if (dom.newChatBtn) {
    dom.newChatBtn.onclick = () => {
        if(isGenerating) return;
        currentSessionId = generateUUID();
        localStorage.setItem('last_session_id', currentSessionId);
        if (dom.chatWindow) dom.chatWindow.innerHTML = '';
        updatePageTitle('新对话');
        renderWelcome();
        loadSessions();
    };
}

if (dom.sendBtn) {
    dom.sendBtn.addEventListener('click', async () => {
        const message = dom.input.value.trim();
        if (!message || isGenerating) return;

        isGenerating = true;
        dom.sendBtn.disabled = true;
        dom.input.value = '';
        
        renderMessage(message, 'user');
        
        const aiContentDiv = renderMessage('Thinking...', 'assistant');
        let fullText = "";
        
        try {
            const response = await fetch('/api/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, session_id: currentSessionId })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let buffer = "";

            if (aiContentDiv) aiContentDiv.innerHTML = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                let lines = buffer.split("\n");
                buffer = lines.pop();

                for (let line of lines) {
                    line = line.trim();
                    if (!line.startsWith("data: ")) continue;
                    try {
                        const data = JSON.parse(line.substring(6));
                        if (data.event === 'token' && data.payload) {
                            fullText += data.payload;
                            if (aiContentDiv) {
                                aiContentDiv.innerHTML = marked.parse(fullText);
                                scrollToBottom();
                            }
                        }
                    } catch (e) {}
                }
            }
            await loadSessions();
            // 重新加载历史以获取后端生成的标题
            const res = await fetch(`/api/v1/chat/sessions/${currentSessionId}`);
            if (res.ok) {
                const data = await res.json();
                updatePageTitle(data.title);
            }
        } catch (error) {
            if (aiContentDiv) aiContentDiv.innerHTML = `<span class="text-red-500">Error: 连接中断</span>`;
        } finally {
            isGenerating = false;
            dom.sendBtn.disabled = false;
            if (dom.input) dom.input.focus();
        }
    });
}

if (dom.uploadBtn && dom.fileInput) {
    dom.uploadBtn.addEventListener('click', () => dom.fileInput.click());
    dom.fileInput.addEventListener('change', async () => {
        if (dom.fileInput.files.length > 0) {
            const file = dom.fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            const loadingDiv = renderMessage(`📄 上传文件: ${file.name}`, 'user');
            
            try {
                const res = await fetch('/api/v1/documents/upload', { method: 'POST', body: formData });
                if (res.ok) {
                    renderMessage(`✅ 文件 **${file.name}** 已解析完成。`, 'assistant');
                } else {
                    renderMessage(`❌ 上传失败`, 'assistant');
                }
            } catch (e) { renderMessage(`❌ 网络错误`, 'assistant'); }
            dom.fileInput.value = '';
        }
    });
}

if (dom.input) {
    dom.input.addEventListener('keypress', (e) => { 
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            dom.sendBtn.click(); 
        }
    });
}

// Init
window.onload = async () => {
    updatePageTitle('新对话');
    renderWelcome();
    await loadSessions();
    const lastId = localStorage.getItem('last_session_id');
    if (lastId) {
        currentSessionId = lastId;
        await loadSessionHistory(lastId);
        await loadSessions(); 
    }
};