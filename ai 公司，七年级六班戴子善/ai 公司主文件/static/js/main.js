// main.js - 多智能体工作流系统前端交互脚本

document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const outputContainer = document.getElementById('output-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const todoList = document.getElementById('todo-list');
    const currentAgentInfo = document.getElementById('current-agent');
    const agentSwitcher = document.getElementById('agent-switcher');
    
    // 当前智能体
    let currentAgent = 'analyst';
    
    // 初始化页面
    initializePage();
    
    // 发送用户输入
    if (sendBtn) {
        sendBtn.addEventListener('click', sendUserRequest);
    }
    
    // 按Enter键发送
    if (userInput) {
        userInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendUserRequest();
            }
        });
    }
    
    // 初始化页面
    function initializePage() {
        // 添加工具栏
        addToolbar();
        
        // 添加智能体切换器
        if (agentSwitcher) {
            createAgentSwitcher();
        }
        
        // 获取初始响应
        fetch('/initialize_workflow', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ auto_start: true })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // 处理流式响应
                handleAgentResponseStream(data.response_id);
                
                // 更新当前智能体
                if (data.current_agent) {
                    currentAgent = data.current_agent;
                    updateCurrentAgentDisplay();
                }
            } else {
                showNotification(data.message || '初始化失败', 'error');
            }
        })
        .catch(error => {
            console.error('初始化请求失败:', error);
            showNotification('网络错误，请重试', 'error');
        });
    }
    
    // 添加工具栏
    function addToolbar() {
        const toolbarContainer = document.createElement('div');
        toolbarContainer.className = 'toolbar';
        
        // 浏览文件按钮
        const browseFilesBtn = document.createElement('button');
        browseFilesBtn.className = 'toolbar-button';
        browseFilesBtn.innerHTML = '<i class="fas fa-folder-open"></i> 浏览文件';
        browseFilesBtn.addEventListener('click', browseFiles);
        
        // 终端命令按钮
        const terminalBtn = document.createElement('button');
        terminalBtn.className = 'toolbar-button';
        terminalBtn.innerHTML = '<i class="fas fa-terminal"></i> 终端命令';
        terminalBtn.addEventListener('click', showCommandPrompt);
        
        // 导出对话按钮
        const exportBtn = document.createElement('button');
        exportBtn.className = 'toolbar-button';
        exportBtn.innerHTML = '<i class="fas fa-download"></i> 导出对话';
        exportBtn.addEventListener('click', exportConversationHistory);
        
        // 系统信息按钮
        const sysInfoBtn = document.createElement('button');
        sysInfoBtn.className = 'toolbar-button';
        sysInfoBtn.innerHTML = '<i class="fas fa-info-circle"></i> 系统信息';
        sysInfoBtn.addEventListener('click', showSystemInfo);
        
        // 添加按钮到工具栏
        toolbarContainer.appendChild(browseFilesBtn);
        toolbarContainer.appendChild(terminalBtn);
        toolbarContainer.appendChild(exportBtn);
        toolbarContainer.appendChild(sysInfoBtn);
        
        // 添加工具栏到页面
        const workflowHeader = document.querySelector('.workflow-header');
        if (workflowHeader) {
            workflowHeader.appendChild(toolbarContainer);
        }
    }
    
    // 创建智能体切换器
    function createAgentSwitcher() {
        const agents = [
            { id: 'analyst', name: '分析官' },
            { id: 'ceo', name: '首席执行官' },
            { id: 'writer', name: '小说家' },
            { id: 'programmer', name: '程序员' },
            { id: 'reviewer', name: '审核员' },
            { id: 'web_searcher', name: '网络搜索员' },  // 添加网络搜索员
            { id: 'file_organizer', name: '文件整理员' }  // 添加文件整理员
        ];
        
        agentSwitcher.innerHTML = '';
        
        agents.forEach(agent => {
            const button = document.createElement('button');
            button.className = `agent-button ${agent.id === currentAgent ? 'active' : ''}`;
            button.textContent = agent.name;
            button.dataset.agent = agent.id;
            
            button.addEventListener('click', function() {
                switchAgent(agent.id);
            });
            
            agentSwitcher.appendChild(button);
        });
    }
    
    // 切换智能体
    function switchAgent(agentId) {
        fetch('/switch_agent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ agent_id: agentId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                currentAgent = agentId;
                updateCurrentAgentDisplay();
                
                // 更新智能体切换器
                const buttons = agentSwitcher.querySelectorAll('.agent-button');
                buttons.forEach(button => {
                    button.classList.toggle('active', button.dataset.agent === agentId);
                });
                
                showNotification(`已切换到${data.agent_name}`, 'success');
            } else {
                showNotification(data.message || '切换智能体失败', 'error');
            }
        })
        .catch(error => {
            console.error('切换智能体失败:', error);
            showNotification('网络错误，请重试', 'error');
        });
    }
    
    // 更新当前智能体显示
    function updateCurrentAgentDisplay() {
        if (currentAgentInfo) {
            currentAgentInfo.textContent = `当前智能体：${getAgentDisplayName(currentAgent)}`;
        }
    }
    
    // 禁用输入
    function disableInput() {
        if (userInput) userInput.disabled = true;
        if (sendBtn) sendBtn.disabled = true;
    }
    
    // 启用输入
    function enableInput() {
        if (userInput) userInput.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        if (userInput) userInput.focus();
    }
    
    // 显示错误
    function showError(message) {
        if (!outputContainer) return;
        
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        outputContainer.appendChild(errorElement);
        outputContainer.scrollTop = outputContainer.scrollHeight;
    }
    
    // 更新待办事项列表
    function updateTodoList(items) {
        if (!todoList) return;
        
        // 清空列表
        todoList.innerHTML = '';
        
        if (items.length === 0) {
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'empty-message';
            emptyMessage.textContent = '暂无待办事项';
            todoList.appendChild(emptyMessage);
            return;
        }
        
        // 添加待办事项
        items.forEach((item, index) => {
            const todoItem = document.createElement('div');
            todoItem.className = 'todo-item';
            
            const statusClass = item.status === 'completed' ? 'status-completed' : 'status-pending';
            const statusText = item.status === 'completed' ? '已完成' : '待处理';
            
            todoItem.innerHTML = `
                <div class="todo-number">任务 #${index + 1}</div>
                <div class="todo-agent">${getAgentDisplayName(item.agent)}</div>
                <div class="todo-description">${item.description}</div>
                <div class="todo-status ${statusClass}">${statusText}</div>
                ${item.status !== 'completed' ? `<button class="complete-task-btn" onclick="completeTask(${index + 1})">完成</button>` : ''}
            `;
            
            todoList.appendChild(todoItem);
        });
    }
    
    // 处理智能体响应流
    function handleAgentResponseStream(responseId) {
        if (!outputContainer) return;
        
        const responseElement = document.createElement('div');
        responseElement.className = 'agent-response fade-in';
        responseElement.innerHTML = `
            <div class="agent-header">
                <div class="agent-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="agent-name">${getAgentDisplayName(currentAgent)} 响应中...</div>
            </div>
            <div class="response-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        outputContainer.appendChild(responseElement);
        outputContainer.scrollTop = outputContainer.scrollHeight;
        
        const responseContent = responseElement.querySelector('.response-content');
        
        // 创建事件源
        const eventSource = new EventSource(`/stream_response/${responseId}`);
        
        // 处理消息
        eventSource.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.text) {
                // 移除打字指示器
                const typingIndicator = responseContent.querySelector('.typing-indicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }
                
                // 添加文本并应用Markdown格式
                if (window.marked) {
                    responseContent.innerHTML += marked.parse(data.text);
                } else {
                    responseContent.innerHTML += data.text;
                }
                
                // 应用代码高亮
                if (window.hljs) {
                    const codeBlocks = responseContent.querySelectorAll('pre code');
                    codeBlocks.forEach(block => {
                        hljs.highlightBlock(block);
                    });
                }
                
                outputContainer.scrollTop = outputContainer.scrollHeight;
            }
            
            if (data.complete) {
                // 更新智能体名称
                const agentHeader = responseElement.querySelector('.agent-name');
                if (agentHeader) {
                    agentHeader.textContent = getAgentDisplayName(currentAgent);
                }
                
                // 关闭事件源
                eventSource.close();
                
                // 更新下一个智能体
                if (data.next_agent) {
                    currentAgent = data.next_agent;
                    updateCurrentAgentDisplay();
                    
                    // 更新智能体切换器
                    if (agentSwitcher) {
                        const buttons = agentSwitcher.querySelectorAll('.agent-button');
                        buttons.forEach(button => {
                            button.classList.toggle('active', button.dataset.agent === currentAgent);
                        });
                    }
                }
                
                // 更新待办事项列表
                if (data.todo_items) {
                    updateTodoList(data.todo_items);
                }
                
                // 启用输入
                enableInput();
            }
        };
        
        // 处理错误
        eventSource.onerror = function(error) {
            console.error('EventSource failed:', error);
            
            // 移除打字指示器
            const typingIndicator = responseContent.querySelector('.typing-indicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            responseContent.innerHTML += '<div class="error-message">连接中断，请刷新页面重试</div>';
            eventSource.close();
            enableInput();
        };
    }
    
    // 发送用户请求
    // 修改这部分代码，使用正确的API路径
    function sendUserRequest() {
        if (!userInput || !outputContainer) return;
        
        const userInputText = userInput.value.trim();
        if (!userInputText) return;
        
        // 显示用户输入
        const userMessage = document.createElement('div');
        userMessage.className = 'user-message fade-in';
        userMessage.innerHTML = `
            <div class="user-avatar">
                <i class="fas fa-user"></i>
            </div>
            <div class="message-content">${window.marked ? marked.parse(userInputText) : userInputText}</div>
        `;
        outputContainer.appendChild(userMessage);
        outputContainer.scrollTop = outputContainer.scrollHeight;
        
        // 禁用输入
        disableInput();
        
        // 发送请求 - 修改为正确的API路径
        fetch('/stream_agent_response', {  // 修改为后端实际定义的路由
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_input: userInputText
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // 处理流式响应
                handleAgentResponseStream(data.response_id);
            } else {
                showError(data.message || '处理请求时出错');
                enableInput();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('网络错误，请重试');
            enableInput();
        });
        
        // 清空输入框
        userInput.value = '';
    }
    
    // 标记任务完成
    window.completeTask = function(taskId) {
        fetch('/complete_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ task_id: taskId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showNotification(data.message, 'success');
                
                // 刷新待办事项列表
                fetch('/get_todo_list')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            updateTodoList(data.todo_items);
                        }
                    });
            } else {
                showNotification(data.message || '标记任务完成失败', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('网络错误，请重试', 'error');
        });
    };
    
    // 浏览文件
    function browseFiles() {
        fetch('/browse_files')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showFileBrowser(data.files);
                } else {
                    showNotification(data.message || '浏览文件失败', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('网络错误，请重试', 'error');
            });
    }
    
    // 显示文件浏览器
    function showFileBrowser(files) {
        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'modal';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        
        // 创建标题
        const title = document.createElement('h2');
        title.textContent = '文件浏览器';
        
        // 创建文件列表
        const fileListElement = document.createElement('div');
        fileListElement.className = 'file-browser-list';
        
        // 添加文件
        files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = `file-browser-item ${file.type}`;
            
            const fileIcon = document.createElement('i');
            fileIcon.className = file.type === 'directory' ? 'fas fa-folder' : 'fas fa-file';
            
            const fileName = document.createElement('span');
            fileName.textContent = file.name;
            
            fileItem.appendChild(fileIcon);
            fileItem.appendChild(fileName);
            
            // 添加点击事件
            fileItem.addEventListener('click', () => {
                if (file.type === 'directory') {
                    // 浏览目录
                    fetch(`/browse_files?path=${encodeURIComponent(file.path)}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success') {
                                // 更新文件列表
                                fileListElement.innerHTML = '';
                                showFileBrowser(data.files);
                            } else {
                                showNotification(data.message || '浏览目录失败', 'error');
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            showNotification('网络错误，请重试', 'error');
                        });
                } else {
                    // 选择文件
                    modal.remove();
                    
                    // 添加文件内容到对话
                    fetch(`/read_file?path=${encodeURIComponent(file.path)}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success') {
                                addFileContentToChat(file.name, file.path, data.content);
                            } else {
                                showNotification(data.message || '读取文件失败', 'error');
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            showNotification('网络错误，请重试', 'error');
                        });
                }
            });
            
            fileListElement.appendChild(fileItem);
        });
        
        // 创建关闭按钮
        const closeButton = document.createElement('button');
        closeButton.className = 'btn secondary';
        closeButton.textContent = '关闭';
        closeButton.addEventListener('click', () => {
            modal.remove();
        });
        
        // 组装模态框
        modalContent.appendChild(title);
        modalContent.appendChild(fileListElement);
        modalContent.appendChild(closeButton);
        modal.appendChild(modalContent);
        
        // 添加到页面
        document.body.appendChild(modal);
    }
    
    // 添加文件内容到对话
    function addFileContentToChat(fileName, filePath, content) {
        if (!outputContainer) return;
        
        const fileElement = document.createElement('div');
        fileElement.className = 'system-message fade-in';
        
        // 确定文件类型和语言
        const fileExtension = fileName.split('.').pop().toLowerCase();
        let language = 'plaintext';
        
        // 根据扩展名设置语言
        const languageMap = {
            'js': 'javascript',
            'py': 'python',
            'html': 'html',
            'css': 'css',
            'json': 'json',
            'md': 'markdown',
            'txt': 'plaintext'
        };
        
        if (languageMap[fileExtension]) {
            language = languageMap[fileExtension];
        }
        
        fileElement.innerHTML = `
            <div class="file-header">
                <i class="fas fa-file-code"></i>
                <span class="file-name">${fileName}</span>
                <span class="file-path">${filePath}</span>
            </div>
            <pre><code class="language-${language}">${escapeHtml(content)}</code></pre>
        `;
        
        outputContainer.appendChild(fileElement);
        
        // 应用代码高亮
        if (window.hljs) {
            const codeBlock = fileElement.querySelector('code');
            hljs.highlightBlock(codeBlock);
        }
        
        outputContainer.scrollTop = outputContainer.scrollHeight;
        showNotification(`已添加文件: ${fileName}`, 'success');
    }
    
    // HTML转义
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    // 显示命令提示符
    function showCommandPrompt() {
        // 创建模态框
        const modal = document.createElement('div');
        modal.className = 'modal';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'modal-content';
        
        // 创建标题
        const title = document.createElement('h2');
        title.textContent = '执行终端命令';
        
        // 创建命令输入
        const commandInput = document.createElement('input');
        commandInput.type = 'text';
        commandInput.placeholder = '输入命令...';
        commandInput.className = 'command-input';
        
        // 创建操作按钮
        const actionButtons = document.createElement('div');
        actionButtons.className = 'modal-actions';
        
        const executeButton = document.createElement('button');
        executeButton.className = 'btn primary';
        executeButton.textContent = '执行';
        executeButton.addEventListener('click', () => {
            const command = commandInput.value.trim();
            if (command) {
                modal.remove();
                executeCommand(command);
            } else {
                showNotification('请输入命令', 'error');
            }
        });
        
        const cancelButton = document.createElement('button');
        cancelButton.className = 'btn secondary';
        cancelButton.textContent = '取消';
        cancelButton.addEventListener('click', () => {
            modal.remove();
        });
        
        // 添加按Enter键执行命令
        commandInput.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                const command = commandInput.value.trim();
                if (command) {
                    modal.remove();
                    executeCommand(command);
                } else {
                    showNotification('请输入命令', 'error');
                }
            }
        });
        
        actionButtons.appendChild(executeButton);
        actionButtons.appendChild(cancelButton);
        
        // 组装模态框
        modalContent.appendChild(title);
        modalContent.appendChild(commandInput);
        modalContent.appendChild(actionButtons);
        modal.appendChild(modalContent);
        
        // 添加到页面
        document.body.appendChild(modal);
        
        // 自动聚焦到输入框
        setTimeout(() => {
            commandInput.focus();
        }, 100);
    }
    
    // 执行命令
    function executeCommand(command) {
        fetch('/execute_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command: command })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showCommandResult(command, data.output);
            } else {
                showNotification(data.message || '执行命令失败', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('网络错误，请重试', 'error');
        });
    }
    
    // 显示命令结果
    function showCommandResult(command, output) {
        if (!outputContainer) return;
        
        // 创建终端输出元素
        const terminalOutput = document.createElement('div');
        terminalOutput.className = 'terminal fade-in';
        
        // 添加命令
        const commandElement = document.createElement('div');
        commandElement.className = 'terminal-command';
        commandElement.innerHTML = `<span class="terminal-prompt">$ </span>${escapeHtml(command)}`;
        
        // 添加输出
        const outputElement = document.createElement('div');
        outputElement.className = 'terminal-output';
        outputElement.textContent = output;
        
        terminalOutput.appendChild(commandElement);
        terminalOutput.appendChild(outputElement);
        
        // 添加到输出容器
        outputContainer.appendChild(terminalOutput);
        outputContainer.scrollTop = outputContainer.scrollHeight;
    }
    
    // 显示系统信息
    function showSystemInfo() {
        fetch('/get_system_info')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    displaySystemInfo(data.system_info);
                } else {
                    showNotification(data.message || '获取系统信息失败', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('网络错误，请重试', 'error');
            });
    }
    
    // 显示系统信息
    function displaySystemInfo(info) {
        if (!outputContainer) return;
        
        const infoElement = document.createElement('div');
        infoElement.className = 'system-message fade-in';
        
        // 格式化内存大小
        const formatBytes = (bytes) => {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        };
        
        // 构建系统信息HTML
        let html = `
            <div class="info-header">
                <i class="fas fa-info-circle"></i>
                <span>系统信息</span>
            </div>
            <div class="info-content">
                <div class="info-item">
                    <span class="info-label">操作系统:</span>
                    <span class="info-value">${info.system} ${info.release}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">主机名:</span>
                    <span class="info-value">${info.hostname}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">处理器:</span>
                    <span class="info-value">${info.processor} (${info.cpu_count} 核)</span>
                </div>
                <div class="info-item">
                    <span class="info-label">内存:</span>
                    <span class="info-value">${formatBytes(info.memory_available)} 可用 / ${formatBytes(info.memory_total)} 总计</span>
                </div>
                <div class="info-item">
                    <span class="info-label">网络接口:</span>
                    <span class="info-value">${info.network_interfaces.join(', ')}</span>
                </div>
            </div>
        `;
        
        infoElement.innerHTML = html;
        outputContainer.appendChild(infoElement);
        outputContainer.scrollTop = outputContainer.scrollHeight;
    }
    
    // 导出对话历史
    function exportConversationHistory() {
        if (!outputContainer) return;
        
        // 获取所有消息
        const messages = outputContainer.querySelectorAll('.user-message, .agent-response');
        
        let exportText = '# 多智能体工作流对话历史\n\n';
        
        messages.forEach(message => {
            if (message.classList.contains('user-message')) {
                const content = message.querySelector('.message-content').textContent;
                exportText += `## 用户\n\n${content}\n\n---\n\n`;
            } else if (message.classList.contains('agent-response')) {
                const header = message.querySelector('.agent-name').textContent;
                const content = message.querySelector('.response-content').textContent;
                exportText += `## ${header}\n\n${content}\n\n---\n\n`;
            }
        });
        
        // 创建下载链接
        const blob = new Blob([exportText], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `对话历史_${new Date().toISOString().slice(0, 10)}.md`;
        a.click();
        
        URL.revokeObjectURL(url);
        
        showNotification('对话历史已导出', 'success');
    }
    
    // 获取智能体显示名称
    function getAgentDisplayName(agentId) {
        const agentNames = {
            'analyst': '分析官',
            'ceo': '首席执行官',
            'writer': '小说家',
            'programmer': '程序员',
            'reviewer': '审核员',
            'web_searcher': '网络搜索员',
            'file_organizer': '文件整理员'
        };
        
        return agentNames[agentId] || agentId;
    }
    
    // 显示通知
    // 添加缺失的 showNotification 函数
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // 3秒后自动移除
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                notification.remove();
            }, 500);
        }, 3000);
    }
    
    // 将函数添加到全局作用域
    window.showNotification = showNotification;
    
    // 添加快捷键支持
    document.addEventListener('keydown', (e) => {
        // Ctrl+B: 浏览文件
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            browseFiles();
        }
        
        // Ctrl+T: 打开终端
        if (e.ctrlKey && e.key === 't') {
            e.preventDefault();
            showCommandPrompt();
        }
        
        // Esc: 关闭所有模态框
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => modal.remove());
        }
    });
    
    // 初始化完成
    console.log('多智能体工作流系统前端初始化完成');
});

// 添加以下代码来确保"开始创作"按钮正确绑定事件
document.addEventListener('DOMContentLoaded', function() {
    // 获取"开始创作"按钮
    const initializeBtn = document.getElementById('initialize-btn');
    
    // 如果按钮存在，绑定点击事件
    if (initializeBtn) {
        initializeBtn.addEventListener('click', function() {
            // 获取用户输入
            const userRequest = document.getElementById('user-request').value.trim();
            
            // 验证用户输入
            if (!userRequest) {
                showNotification('请输入创作需求', 'error');
                return;
            }
            
            // 禁用按钮，防止重复提交
            initializeBtn.disabled = true;
            initializeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 处理中...';
            
            // 发送初始化请求
            fetch('/initialize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_request: userRequest
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // 隐藏初始化面板，显示工作流面板
                    document.getElementById('setup-panel').classList.add('hidden');
                    document.getElementById('workflow-panel').classList.remove('hidden');
                    
                    // 更新当前智能体显示
                    updateCurrentAgentDisplay(data.current_agent);
                    
                    // 显示成功消息
                    showNotification('工作流初始化成功', 'success');
                } else {
                    // 显示错误消息
                    showNotification(data.message || '初始化失败', 'error');
                    
                    // 重新启用按钮
                    initializeBtn.disabled = false;
                    initializeBtn.innerHTML = '<i class="fas fa-play"></i> 开始创作';
                }
            })
            .catch(error => {
                console.error('初始化请求失败:', error);
                showNotification('网络错误，请重试', 'error');
                
                // 重新启用按钮
                initializeBtn.disabled = false;
                initializeBtn.innerHTML = '<i class="fas fa-play"></i> 开始创作';
            });
        });
    }
    
    // 添加缺失的showNotification函数
    if (typeof window.showNotification !== 'function') {
        window.showNotification = function(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            // 3秒后自动移除
            setTimeout(() => {
                notification.classList.add('fade-out');
                setTimeout(() => {
                    notification.remove();
                }, 500);
            }, 3000);
        };
    }
});
// 修改流式响应处理函数
function handleStreamResponse(responseId, agentId) {
    const responseContainer = document.getElementById('response-container');
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 正在生成响应...';
    responseContainer.appendChild(loadingIndicator);
    
    // 创建新的响应元素
    const responseElement = document.createElement('div');
    responseElement.className = 'agent-response';
    responseElement.dataset.agent = agentId;
    responseContainer.appendChild(responseElement);
    
    // 使用EventSource进行SSE连接
    const eventSource = new EventSource(`/stream_response/${responseId}`);
    let responseText = '';
    
    // 处理消息事件
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // 移除加载指示器
        if (loadingIndicator.parentNode) {
            loadingIndicator.remove();
        }
        
        // 处理文本更新
        if (data.text) {
            responseText += data.text;
            responseElement.innerHTML = marked.parse(responseText);
            // 自动滚动到底部
            window.scrollTo(0, document.body.scrollHeight);
        }
        
        // 处理完成事件
        if (data.complete) {
            eventSource.close();
            
            // 更新当前智能体
            if (data.next_agent) {
                updateCurrentAgentDisplay(data.next_agent, data.next_agent_name);
            }
            
            // 更新待办事项列表
            if (data.todo_items) {
                updateTodoList(data.todo_items);
            }
            
            // 启用输入框和发送按钮
            document.getElementById('user-input').disabled = false;
            document.getElementById('send-button').disabled = false;
        }
    };
    
    // 处理错误
    eventSource.onerror = function(error) {
        console.error('EventSource failed:', error);
        eventSource.close();
        
        // 显示错误消息
        responseElement.innerHTML += '<div class="error-message">连接中断，请刷新页面重试</div>';
        
        // 启用输入框和发送按钮
        document.getElementById('user-input').disabled = false;
        document.getElementById('send-button').disabled = false;
    };
}