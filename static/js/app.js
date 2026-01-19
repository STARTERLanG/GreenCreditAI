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

// --- State ---
let currentSessionId = localStorage.getItem('last_session_id') || generateUUID();
let isGenerating = false;

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
    searchBtn: document.getElementById('search-btn')
};

// --- Sidebar Logic ---
let isSidebarCollapsed = false;

if (dom.sidebarToggle) {
    dom.sidebarToggle.onclick = () => {
        isSidebarCollapsed = !isSidebarCollapsed;
        
        if (isSidebarCollapsed) {
            dom.sidebar.classList.replace('w-[280px]', 'w-20');
            dom.toggleIcon.classList.add('rotate-180');
            document.querySelectorAll('.sidebar-text').forEach(el => el.classList.add('hidden'));
            if (dom.searchBtn) dom.searchBtn.classList.add('hidden');
            
            dom.newChatBtn.classList.remove('px-4', 'space-x-2');
            dom.newChatBtn.classList.add('justify-center', 'px-0');
        } else {
            dom.sidebar.classList.replace('w-20', 'w-[280px]');
            dom.toggleIcon.classList.remove('rotate-180');
            document.querySelectorAll('.sidebar-text').forEach(el => el.classList.remove('hidden'));
            if (dom.searchBtn) dom.searchBtn.classList.remove('hidden');
            
            dom.newChatBtn.classList.add('px-4', 'space-x-2');
            dom.newChatBtn.classList.remove('justify-center', 'px-0');
        }
    };
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
                div.className = `group px-3 py-2.5 rounded-xl cursor-pointer flex items-center space-x-3 mb-1 transition-all duration-200 ${isActive ? 'bg-white shadow-sm text-emerald-800 font-bold border border-[#d1e2da]' : 'text-[#2d4a43]/70 hover:bg-white/40 hover:text-[#2d4a43]'}`;
                
                const textClass = isSidebarCollapsed ? 'hidden sidebar-text' : 'sidebar-text';
                
                div.innerHTML = `
                    <i class="fas fa-comment-alt text-xs ${isActive ? 'text-emerald-500' : 'text-[#2d4a43]/40 group-hover:text-emerald-500'} flex-shrink-0"></i>
                    <span class="text-sm truncate flex-1 ${textClass}">${s.title || '新对话'}</span>
                `;
                div.onclick = () => switchToSession(s.id);
                dom.sessionList.appendChild(div);
            });
        }
    } catch(e) { console.error(e); }
}

async function loadSessionHistory(id) {
    try {
        const res = await fetch(`/api/v1/chat/sessions/${id}`);
        if (!res.ok) {
            console.error("Session not found");
            renderWelcome();
            return;
        }
        const data = await res.json();
        
        if (dom.chatWindow) dom.chatWindow.innerHTML = ''; 
        
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
            loadSessions();
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
    renderWelcome();
    await loadSessions();
    const lastId = localStorage.getItem('last_session_id');
    if (lastId) {
        currentSessionId = lastId;
        await loadSessionHistory(lastId);
        await loadSessions(); 
    }
};