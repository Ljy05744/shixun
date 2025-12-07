/**
 * AI增强型任务管理系统 - 前端逻辑
 */

// API基础URL
const API_BASE_URL = 'http://localhost:8080/api';

// 当前编辑的任务ID
let currentEditTaskId = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    loadTasks();
    loadStats();

    // 设置明天为默认日期（可选）
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('taskDueDate').value = tomorrow.toISOString().split('T')[0];
});

// 加载任务列表
async function loadTasks() {
    const statusFilter = document.getElementById('statusFilter').value;
    const container = document.getElementById('tasksContainer');
    const emptyState = document.getElementById('emptyState');

    container.innerHTML = `
        <div class="text-center py-8 text-gray-500">
            <i class="fas fa-spinner fa-spin text-2xl mb-3"></i>
            <p>加载任务中...</p>
        </div>
    `;

    try {
        const url = statusFilter
            ? `${API_BASE_URL}/tasks?status=${statusFilter}`
            : `${API_BASE_URL}/tasks`;

        const response = await fetch(url);
        const tasks = await response.json();

        if (tasks.length === 0) {
            container.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');
        container.innerHTML = '';

        tasks.forEach(task => {
            container.appendChild(createTaskCard(task));
        });

    } catch (error) {
        console.error('加载任务失败:', error);
        container.innerHTML = `
            <div class="text-center py-8 text-red-500">
                <i class="fas fa-exclamation-triangle text-2xl mb-3"></i>
                <p>加载任务失败，请检查网络连接</p>
                <button onclick="loadTasks()" class="mt-2 text-blue-600 hover:text-blue-800">
                    重试
                </button>
            </div>
        `;
    }
}

// 创建任务卡片
function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = `task-card priority-${task.priority} bg-white rounded-lg border border-gray-200 p-5`;
    card.id = `task-${task.id}`;

    // 格式化日期
    const dueDate = task.due_date ? new Date(task.due_date).toLocaleDateString('zh-CN') : '未设置';
    const createdDate = new Date(task.created_at).toLocaleDateString('zh-CN');

    // 状态标签
    const statusText = {
        'pending': '待处理',
        'in_progress': '进行中',
        'completed': '已完成'
    }[task.status];

    const statusClass = {
        'pending': 'status-pending',
        'in_progress': 'status-in_progress',
        'completed': 'status-completed'
    }[task.status];

    // 优先级标签
    const priorityText = ['极高', '高', '中', '低', '极低'][task.priority - 1];

    card.innerHTML = `
        <div class="flex justify-between items-start">
            <div class="flex-1">
                <div class="flex items-center mb-2">
                    <h3 class="text-lg font-semibold text-gray-800 mr-3">${task.title}</h3>
                    <span class="text-xs px-2 py-1 rounded-full ${statusClass}">
                        ${statusText}
                    </span>
                </div>

                ${task.description ? `<p class="text-gray-600 mb-3">${task.description}</p>` : ''}

                <div class="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                    <div class="flex items-center">
                        <i class="fas fa-calendar-alt mr-2"></i>
                        <span>截止: ${dueDate}</span>
                    </div>
                    <div class="flex items-center">
                        <i class="fas fa-flag mr-2"></i>
                        <span>优先级: ${priorityText} (${task.priority})</span>
                    </div>
                    <div class="flex items-center">
                        <i class="fas fa-clock mr-2"></i>
                        <span>创建: ${createdDate}</span>
                    </div>
                </div>
            </div>

            <div class="flex space-x-2 ml-4">
                <button onclick="toggleTaskStatus(${task.id}, '${task.status}')"
                        class="px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded transition duration-200">
                    ${task.status === 'completed' ? '标记未完成' : '标记完成'}
                </button>

                <button onclick="openEditModal(${task.id})"
                        class="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition duration-200">
                    <i class="fas fa-edit"></i>
                </button>

                <button onclick="deleteTask(${task.id})"
                        class="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded transition duration-200">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;


        // 在操作按钮区域添加AI优先级推荐按钮
    card.innerHTML = `
        <div class="flex justify-between items-start">
            <div class="flex-1">
                <div class="flex items-center mb-2">
                    <h3 class="text-lg font-semibold text-gray-800 mr-3">${task.title}</h3>
                    <span class="text-xs px-2 py-1 rounded-full ${statusClass}">
                        ${statusText}
                    </span>
                    <!-- 新增：优先级指示器 -->
                    <span class="ml-2 px-2 py-1 text-xs rounded-full ${getPriorityColorClass(task.priority)}">
                        ${priorityText} (${task.priority})
                    </span>
                </div>
                <!-- ... 其他现有内容 ... -->
            </div>

            <div class="flex space-x-2 ml-4">
                <!-- 新增：AI优先级推荐按钮 -->
                <button onclick="showPriorityRecommendation(${task.id})"
                        class="px-3 py-1 bg-purple-100 hover:bg-purple-200 text-purple-700 rounded transition duration-200"
                        title="AI推荐优先级">
                    <i class="fas fa-lightbulb"></i>
                </button>

                <!-- 现有按钮 -->
                <button onclick="toggleTaskStatus(${task.id}, '${task.status}')"
                        class="px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded transition duration-200">
                    ${task.status === 'completed' ? '标记未完成' : '标记完成'}
                </button>

                <button onclick="openEditModal(${task.id})"
                        class="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded transition duration-200">
                    <i class="fas fa-edit"></i>
                </button>

                <button onclick="deleteTask(${task.id})"
                        class="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded transition duration-200">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;

    return card;
}

// 新增：获取优先级颜色类
function getPriorityColorClass(priority) {
    switch(priority) {
        case 1: return 'bg-red-100 text-red-800';
        case 2: return 'bg-orange-100 text-orange-800';
        case 3: return 'bg-yellow-100 text-yellow-800';
        case 4: return 'bg-blue-100 text-blue-800';
        case 5: return 'bg-gray-100 text-gray-800';
        default: return 'bg-gray-100 text-gray-800';
    }
}

// 新增：显示AI优先级推荐
async function showPriorityRecommendation(taskId) {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/priority-recommendation`);
        const recommendation = await response.json();

        // 创建推荐弹窗
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-xl shadow-2xl w-full max-w-md p-6 m-4">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center">
                        <div class="p-2 bg-purple-100 rounded-lg mr-3">
                            <i class="fas fa-robot text-purple-600"></i>
                        </div>
                        <h3 class="text-lg font-semibold text-gray-800">AI优先级推荐</h3>
                    </div>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" 
                            class="text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>

                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div class="text-center p-4 bg-gray-50 rounded-lg">
                            <div class="text-sm text-gray-500 mb-1">当前优先级</div>
                            <div class="text-2xl font-bold ${getPriorityColorClass(recommendation.current_priority).split(' ')[0]}">
                                ${recommendation.current_priority}
                            </div>
                            <div class="text-xs mt-1">${['极高','高','中','低','极低'][recommendation.current_priority-1]}</div>
                        </div>
                        <div class="text-center p-4 bg-purple-50 rounded-lg border-2 border-purple-200">
                            <div class="text-sm text-gray-500 mb-1">AI推荐</div>
                            <div class="text-2xl font-bold ${getPriorityColorClass(recommendation.recommended_priority).split(' ')[0]}">
                                ${recommendation.recommended_priority}
                            </div>
                            <div class="text-xs mt-1">${['极高','高','中','低','极低'][recommendation.recommended_priority-1]}</div>
                        </div>
                    </div>

                    <div class="p-3 bg-blue-50 rounded-lg">
                        <div class="flex items-start">
                            <i class="fas fa-info-circle text-blue-500 mt-1 mr-2"></i>
                            <div>
                                <div class="font-medium text-blue-800 mb-1">推荐理由</div>
                                <div class="text-sm text-blue-700">${recommendation.reason}</div>
                            </div>
                        </div>
                    </div>

                    <div class="flex items-center justify-between text-sm text-gray-600">
                        <span>AI置信度: <span class="font-semibold">${Math.round(recommendation.confidence * 100)}%</span></span>
                        <div class="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div class="h-full bg-green-500" style="width: ${recommendation.confidence * 100}%"></div>
                        </div>
                    </div>

                    <div class="flex space-x-3 pt-4 border-t border-gray-200">
                        <button onclick="applyPriorityRecommendation(${taskId})"
                                class="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-medium py-3 rounded-lg transition duration-200 flex items-center justify-center">
                            <i class="fas fa-check mr-2"></i>
                            应用推荐
                        </button>
                        <button onclick="this.parentElement.parentElement.parentElement.parentElement.remove()"
                                class="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium py-3 rounded-lg transition duration-200">
                            稍后再说
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    } catch (error) {
        console.error('获取AI推荐失败:', error);
        showNotification('获取AI推荐失败', 'error');
    }
}

// 新增：应用AI优先级推荐
async function applyPriorityRecommendation(taskId) {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/auto-prioritize`, {
            method: 'PUT'
        });

        if (response.ok) {
            showNotification('AI已自动调整任务优先级', 'success');
            loadTasks(); // 重新加载更新显示

            // 关闭弹窗
            const modal = document.querySelector('.fixed.inset-0');
            if (modal) modal.remove();
        }
    } catch (error) {
        console.error('应用推荐失败:', error);
        showNotification('应用推荐失败', 'error');
    }
}

// 创建新任务
async function createTask() {
    const title = document.getElementById('taskTitle').value.trim();
    const description = document.getElementById('taskDescription').value.trim();
    const dueDate = document.getElementById('taskDueDate').value;
    const priority = parseInt(document.getElementById('taskPriority').value);

    if (!title) {
        alert('请输入任务标题');
        return;
    }

    const taskData = {
        title: title,
        description: description || '',
        status: 'pending',
        due_date: dueDate || null,
        priority: priority
    };

    try {
        const response = await fetch(`${API_BASE_URL}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });

        if (!response.ok) throw new Error('创建失败');

        // 清空表单
        document.getElementById('taskTitle').value = '';
        document.getElementById('taskDescription').value = '';
        document.getElementById('taskPriority').value = '3';

        // 重新加载任务列表
        loadTasks();
        loadStats();

        // 显示成功消息
        showNotification('任务创建成功', 'success');

    } catch (error) {
        console.error('创建任务失败:', error);
        showNotification('创建任务失败', 'error');
    }
}

// 使用AI解析自然语言
async function parseWithAI() {
    const text = document.getElementById('aiInput').value.trim();

    if (!text) {
        alert('请输入要解析的自然语言');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/ai/parse`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        });

        if (!response.ok) throw new Error('AI解析失败');

        const result = await response.json();

        // 显示解析结果
        document.getElementById('aiTitle').textContent = result.title;
        document.getElementById('aiDescription').textContent = result.description || '无';
        document.getElementById('aiDueDate').textContent = result.due_date || '未设置';
        document.getElementById('aiPriority').textContent = result.priority;

        // 保存解析结果到data属性
        document.getElementById('aiResult').dataset.parsedData = JSON.stringify(result);
        document.getElementById('aiResult').classList.remove('hidden');

        // 清空输入框
        document.getElementById('aiInput').value = '';

    } catch (error) {
        console.error('AI解析失败:', error);
        showNotification('AI解析失败，请稍后重试', 'error');
    }
}

// 修改：在 loadStats 函数中添加优先级分布显示
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const stats = await response.json();

        // 更新现有统计卡片
        document.getElementById('total-tasks').textContent = stats.total;
        document.getElementById('completed-tasks').textContent = stats.completed;
        document.getElementById('inprogress-tasks').textContent = stats.in_progress;
        document.getElementById('completion-rate').textContent = `${stats.completion_rate}%`;

        // 新增：显示高优先级任务数
        const statsContainer = document.getElementById('stats');
        statsContainer.innerHTML = `
            <div class="flex items-center space-x-4">
                <span class="flex items-center">
                    <i class="fas fa-tasks text-gray-500 mr-2"></i>
                    <span>总任务: ${stats.total}</span>
                </span>
                <span class="flex items-center">
                    <i class="fas fa-flag text-red-500 mr-2"></i>
                    <span>高优先级: ${stats.high_priority_tasks || 0}</span>
                </span>
                <span class="flex items-center">
                    <i class="fas fa-clock text-yellow-500 mr-2"></i>
                    <span>逾期: ${stats.overdue}</span>
                </span>
            </div>
        `;
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// 使用AI解析结果
function useAIParseResult() {
    const resultElement = document.getElementById('aiResult');
    const resultData = JSON.parse(resultElement.dataset.parsedData);

    // 填充到常规表单
    document.getElementById('taskTitle').value = resultData.title;
    document.getElementById('taskDescription').value = resultData.description || '';
    document.getElementById('taskDueDate').value = resultData.due_date || '';
    document.getElementById('taskPriority').value = result}