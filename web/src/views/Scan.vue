<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import {
  scanDirectory as apiScan,
  listTasks,
  getTask,
  deleteTask,
  executeTaskPlan,
  rollbackTask,
} from "@/api/scan";
import BaseConfirmDialog from "@/components/core/BaseConfirmDialog.vue";

const path = ref("");
const loading = ref(false);
const tasks = ref([]);
const selectedTaskId = ref(null);
const selectedTask = ref(null);
const message = ref({ type: "", text: "" });
const showConfirmDialog = ref(false);
const confirmMessage = ref("");
const confirmCallback = ref(null);

let taskPollingIntervals = {};

// 统计信息
const stats = computed(() => ({
  total: tasks.value.length,
  running: tasks.value.filter(t => t.status === 'running').length,
  completed: tasks.value.filter(t => t.status === 'completed').length,
  failed: tasks.value.filter(t => t.status === 'failed').length,
}));

// 加载任务列表
const loadTasks = async () => {
  try {
    tasks.value = await listTasks();
    // 自动选中第一个任务
    if (tasks.value.length > 0 && !selectedTaskId.value) {
      selectTask(tasks.value[0].id);
    }
  } catch (e) {
    console.error("Failed to load tasks:", e);
  }
};

// 轮询指定任务状态
const startTaskPolling = (taskId) => {
  if (taskPollingIntervals[taskId]) return;

  taskPollingIntervals[taskId] = setInterval(async () => {
    try {
      const task = await getTask(taskId);
      
      const index = tasks.value.findIndex((t) => t.id === taskId);
      if (index !== -1) {
        tasks.value[index] = task;
      }
      
      if (selectedTaskId.value === taskId) {
        selectedTask.value = task;
        
        setTimeout(() => {
          const logContainer = document.getElementById("log-container");
          if (logContainer) {
            logContainer.scrollTop = logContainer.scrollHeight;
          }
        }, 50);
      }

      if (task.status === "completed" || task.status === "failed") {
        stopTaskPolling(taskId);
      }
    } catch (e) {
      console.error(`Failed to poll task ${taskId}:`, e);
    }
  }, 1000);
};

const stopTaskPolling = (taskId) => {
  if (taskPollingIntervals[taskId]) {
    clearInterval(taskPollingIntervals[taskId]);
    delete taskPollingIntervals[taskId];
  }
};

const stopAllPolling = () => {
  Object.keys(taskPollingIntervals).forEach(stopTaskPolling);
};

// 创建扫描任务
const scanDirectory = async () => {
  if (!path.value) return;
  loading.value = true;
  message.value = { type: "", text: "" };

  try {
    const { task_id } = await apiScan(path.value);
    
    message.value = {
      type: "success",
      text: `✨ 任务创建成功`,
    };
    
    await loadTasks();
    selectTask(task_id);
    startTaskPolling(task_id);
    
    path.value = "";
  } catch (e) {
    message.value = {
      type: "error",
      text: "❌ " + (e.message || "未知错误"),
    };
  } finally {
    loading.value = false;
  }
};

// 选中任务
const selectTask = async (taskId) => {
  selectedTaskId.value = taskId;
  try {
    selectedTask.value = await getTask(taskId);
    
    if (selectedTask.value.status === "running" || selectedTask.value.status === "pending") {
      startTaskPolling(taskId);
    }
  } catch (e) {
    console.error("Failed to load task details:", e);
  }
};

// 执行任务
const confirmExecute = () => {
  if (!selectedTask.value) return;
  confirmMessage.value = `确定要执行 ${selectedTask.value.file_count} 个文件的重命名吗？`;
  confirmCallback.value = executeInternal;
  showConfirmDialog.value = true;
};

const executeInternal = async () => {
  if (!selectedTask.value) return;
  loading.value = true;
  try {
    await executeTaskPlan(selectedTask.value.id);
    message.value = { type: "success", text: "✅ 执行成功" };
    await loadTasks();
    await selectTask(selectedTask.value.id);
  } catch (e) {
    message.value = {
      type: "error",
      text: "❌ " + (e.message || "未知错误"),
    };
  } finally {
    loading.value = false;
  }
};

// 回滚任务
const confirmRollback = () => {
  confirmMessage.value = "确定要撤销所有更改吗？";
  confirmCallback.value = rollbackInternal;
  showConfirmDialog.value = true;
};

const rollbackInternal = async () => {
  if (!selectedTask.value) return;
  loading.value = true;
  try {
    await rollbackTask(selectedTask.value.id);
    message.value = { type: "success", text: "↩️ 已撤销" };
    await loadTasks();
    await selectTask(selectedTask.value.id);
  } catch (e) {
    message.value = {
      type: "error",
      text: "❌ " + (e.message || "未知错误"),
    };
  } finally {
    loading.value = false;
  }
};

// 删除任务
const confirmDelete = (taskId) => {
  confirmMessage.value = "确定要删除此任务吗？";
  confirmCallback.value = async () => {
    try {
      await deleteTask(taskId);
      message.value = { type: "success", text: "🗑️ 已删除" };
      
      // 如果删除的是当前选中的任务，选中第一个
      if (selectedTaskId.value === taskId) {
        selectedTaskId.value = null;
        selectedTask.value = null;
      }
      
      await loadTasks();
    } catch (e) {
      message.value = {
        type: "error",
        text: "❌ " + (e.message || "未知错误"),
      };
    }
  };
  showConfirmDialog.value = true;
};

// 格式化时间（数据库已存储北京时间）
const formatTime = (isoString) => {
  if (!isoString) return "-";
  const date = new Date(isoString);
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);
  
  if (diff < 60) return `${diff}秒前`;
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
  
  // 超过一天显示日期时间
  return date.toLocaleString("zh-CN", { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  });
};

// 获取状态配置
const getStatusConfig = (status) => {
  const configs = {
    pending: { 
      icon: "⏳", 
      text: "等待中", 
      color: "text-slate-600 dark:text-slate-300",
      bg: "bg-slate-100 dark:bg-slate-700/50"
    },
    running: { 
      icon: "⚡", 
      text: "运行中", 
      color: "text-blue-600 dark:text-blue-300",
      bg: "bg-blue-100 dark:bg-blue-900/30"
    },
    completed: { 
      icon: "✨", 
      text: "已完成", 
      color: "text-emerald-600 dark:text-emerald-300",
      bg: "bg-emerald-100 dark:bg-emerald-900/30"
    },
    failed: { 
      icon: "💥", 
      text: "失败", 
      color: "text-rose-600 dark:text-rose-300",
      bg: "bg-rose-100 dark:bg-rose-900/30"
    },
  };
  return configs[status] || configs.pending;
};

onMounted(() => {
  loadTasks();
});

onUnmounted(() => {
  stopAllPolling();
});
</script>

<template>
  <div class="h-full flex flex-col gap-6">
    <!-- 确认对话框 -->
    <BaseConfirmDialog
      :show="showConfirmDialog"
      :message="confirmMessage"
      @update:show="showConfirmDialog = $event"
      @confirm="confirmCallback"
    />

    <!-- 页面标题 -->
    <div class="flex-shrink-0">
      <div class="flex items-center gap-3">
        <span class="w-2 h-10 bg-cyan-500 rounded-full shadow-lg shadow-cyan-500/30"></span>
        <div>
          <h1 class="text-4xl font-black text-slate-800 dark:text-white tracking-tight">智能扫描</h1>
          <p class="text-xs font-bold text-slate-400 mt-1 uppercase tracking-widest">Smart Scan</p>
        </div>
      </div>
    </div>

    <!-- 扫描输入区 -->
    <div class="flex-shrink-0">
      <div class="bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2rem] p-6 border border-white/60 dark:border-white/10 shadow-xl">
        <div class="flex items-center gap-3 mb-5">
          <div class="p-2.5 rounded-2xl bg-cyan-500 text-white shadow-lg shadow-cyan-500/30">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <div>
            <h2 class="text-lg font-black text-slate-900 dark:text-white tracking-tight">扫描目录</h2>
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Scan Directory</p>
          </div>
        </div>

        <div class="flex gap-3">
          <div class="relative flex-1">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <svg class="h-5 w-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
            <input
              type="text"
              v-model="path"
              placeholder="输入目录路径,例如:D:\Anime\Frieren"
              class="pl-12 pr-4 block w-full rounded-2xl border-0 bg-slate-50/50 dark:bg-black/20 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200/50 dark:ring-white/10 focus:ring-2 focus:ring-inset focus:ring-cyan-500 text-sm py-4 transition-all placeholder:text-slate-400 font-medium"
              @keyup.enter="scanDirectory"
            />
          </div>
          
          <button
            @click="scanDirectory"
            :disabled="loading || !path"
            class="relative overflow-hidden px-8 py-4 rounded-2xl font-bold text-sm text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-95 shadow-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 hover:shadow-2xl hover:shadow-cyan-500/30"
          >
            <div class="relative flex items-center gap-2">
              <svg v-if="!loading" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <svg v-else class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>{{ loading ? "扫描中" : "开始扫描" }}</span>
            </div>
          </button>
        </div>

        <!-- 消息提示 -->
        <transition name="slide-fade">
          <div v-if="message.text" class="mt-4 p-4 rounded-2xl font-bold text-sm flex items-center gap-3"
            :class="{
              'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20': message.type === 'success',
              'bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20': message.type === 'error',
            }">
            <svg v-if="message.type === 'success'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ message.text }}</span>
          </div>
        </transition>
      </div>
    </div>

    <!-- 主内容区 - 左右分栏 -->
    <div class="flex-1 flex gap-4 min-h-0">
      <!-- 左侧任务列表 -->
      <div class="w-80 flex-shrink-0 flex flex-col bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-2xl border border-white/60 dark:border-white/10 shadow-lg overflow-hidden">
        <div class="px-4 py-3 border-b border-slate-200/50 dark:border-white/10 flex-shrink-0">
          <h3 class="font-bold text-slate-900 dark:text-white">任务列表 ({{ stats.total }})</h3>
        </div>
        
        <div class="flex-1 overflow-y-auto p-3 space-y-2">
          <div v-if="tasks.length === 0" class="flex items-center justify-center h-full text-slate-400 text-sm">
            暂无任务
          </div>
          
          <div
            v-for="task in tasks"
            :key="task.id"
            @click="selectTask(task.id)"
            class="group relative cursor-pointer p-3 rounded-xl transition-all hover:shadow-md"
            :class="selectedTaskId === task.id 
              ? 'bg-cyan-500/10 ring-2 ring-cyan-500/50' 
              : 'bg-white/60 dark:bg-slate-800/60 hover:bg-white dark:hover:bg-slate-800'"
          >
            <div class="flex items-start justify-between gap-2 mb-2">
              <div class="flex items-center gap-2 min-w-0 flex-1">
                <div :class="[getStatusConfig(task.status).bg, 'px-2 py-1 rounded-lg flex items-center gap-1.5']">
                  <span class="text-base flex-shrink-0">{{ getStatusConfig(task.status).icon }}</span>
                  <span class="text-xs font-bold truncate" :class="getStatusConfig(task.status).color">
                    {{ getStatusConfig(task.status).text }}
                  </span>
                </div>
                <span class="text-xs text-slate-500 dark:text-slate-400 flex-shrink-0">{{ formatTime(task.start_time) }}</span>
              </div>
              <button
                @click.stop="confirmDelete(task.id)"
                class="flex-shrink-0 p-1 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-500/10 transition-all opacity-0 group-hover:opacity-100"
              >
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
            
            <p class="font-mono text-xs text-slate-600 dark:text-slate-300 truncate mb-1" :title="task.directory_path">
              {{ task.directory_path }}
            </p>
            
            <div class="flex items-center gap-2 text-xs">
              <span v-if="task.file_count > 0" class="text-slate-500 dark:text-slate-400">
                {{ task.file_count }} 文件
              </span>
              <span v-if="task.executed" class="text-emerald-600 dark:text-emerald-400">✓ 已执行</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧任务详情 -->
      <div class="flex-1 flex flex-col bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-2xl border border-white/60 dark:border-white/10 shadow-lg overflow-hidden">
        <div v-if="!selectedTask" class="flex items-center justify-center h-full text-slate-400">
          <div class="text-center">
            <svg class="h-16 w-16 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="text-sm">选择一个任务查看详情</p>
          </div>
        </div>

        <div v-else class="flex flex-col h-full">
          <!-- 标题栏 -->
          <div class="px-6 py-4 border-b border-slate-200/50 dark:border-white/10 flex-shrink-0 bg-slate-50/50 dark:bg-slate-800/50">
            <div class="flex items-start justify-between">
              <div class="flex-1 min-w-0">
                <h3 class="text-lg font-bold text-slate-900 dark:text-white truncate">
                  {{ selectedTask.directory_path }}
                </h3>
                <p class="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  ID: {{ selectedTask.id.substring(0, 12) }}...
                </p>
              </div>
              <div class="flex items-center gap-2 ml-4 flex-shrink-0">
                <button
                  v-if="selectedTask.status === 'completed' && !selectedTask.executed && selectedTask.file_count > 0"
                  @click="confirmExecute"
                  :disabled="loading"
                  class="px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold text-sm shadow-lg hover:shadow-xl transition-all active:scale-95 disabled:opacity-50"
                >
                  ✅ 执行
                </button>
                <button
                  v-if="selectedTask.executed"
                  @click="confirmRollback"
                  :disabled="loading"
                  class="px-4 py-2 rounded-lg bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold text-sm hover:bg-slate-300 dark:hover:bg-slate-600 transition-all active:scale-95"
                >
                  ↩️ 撤销
                </button>
              </div>
            </div>
          </div>

          <!-- 内容区 -->
          <div class="flex-1 overflow-y-auto p-6 space-y-4">
            <!-- 日志区 -->
            <div v-if="selectedTask.logs && selectedTask.logs.length > 0" class="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700">
              <div class="px-4 py-3 bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
                <h4 class="font-bold text-sm text-slate-900 dark:text-white">
                  扫描日志 ({{ selectedTask.logs.length }})
                </h4>
              </div>
              <div id="log-container" class="p-3 bg-slate-950 font-mono text-xs max-h-80 overflow-y-auto space-y-0.5">
                <div v-for="(log, index) in selectedTask.logs" :key="index" class="flex gap-2 opacity-90">
                  <span class="text-slate-600 flex-shrink-0 w-16 text-[10px]">{{ new Date(log.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }}</span>
                  <span :class="{
                    'text-cyan-400': log.level === 'info',
                    'text-emerald-400': log.level === 'success',
                    'text-yellow-400': log.level === 'warning',
                    'text-rose-400': log.level === 'error',
                  }" class="flex-1 text-[11px] leading-relaxed">{{ log.message }}</span>
                </div>
              </div>
            </div>

            <!-- 文件列表 -->
            <div v-if="selectedTask.plan && selectedTask.plan.length > 0" class="rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700">
              <div class="px-4 py-3 bg-slate-100 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
                <h4 class="font-bold text-sm text-slate-900 dark:text-white">
                  文件列表 ({{ selectedTask.plan.length }})
                </h4>
              </div>
              <div class="max-h-96 overflow-y-auto">
                <div v-for="(item, index) in selectedTask.plan" :key="index"
                  class="px-4 py-3 border-b border-slate-100 dark:border-slate-800 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                  <div class="flex items-start gap-2">
                    <div class="flex-shrink-0 mt-0.5">
                      <div v-if="selectedTask.executed" class="w-4 h-4 rounded-full bg-emerald-500 flex items-center justify-center">
                        <svg class="h-2.5 w-2.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                        </svg>
                      </div>
                      <div v-else class="w-4 h-4 rounded-full border-2 border-slate-300 dark:border-slate-600"></div>
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-[10px] text-slate-500 dark:text-slate-400 mb-0.5">原始</p>
                      <p class="font-mono text-xs text-slate-600 dark:text-slate-300 truncate">
                        {{ item.original_path.split("\\").pop() }}
                      </p>
                      <p class="text-[10px] text-emerald-600 dark:text-emerald-400 mt-1.5 mb-0.5">→ 新名称</p>
                      <p class="font-mono text-xs text-emerald-700 dark:text-emerald-300 font-semibold truncate">
                        {{ item.display_path || item.new_path.split("\\").pop() }}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from, .slide-fade-leave-to {
  transform: translateY(-5px);
  opacity: 0;
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}

.dark ::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
}

.dark ::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.4);
}
</style>
