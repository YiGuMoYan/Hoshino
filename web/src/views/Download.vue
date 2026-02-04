<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { listDownloads, addMagnetTask, previewTorrent, retryTask, addTorrentTask, deleteTask } from "@/api/downloads";
import BaseConfirmDialog from "@/components/core/BaseConfirmDialog.vue";
import { useToast } from "@/composables/useToast";

const toast = useToast();
const tasks = ref([]);
const loading = ref(false);
const previewing = ref(false);

const inputType = ref("magnet"); // 'magnet' or 'file'
const showAdvanced = ref(false);
const showPreviewModal = ref(false);
const previewFiles = ref([]);
const previewHash = ref("");

// Log Modal State
const showLogModal = ref(false);
const currentLog = ref("");

// Add Task Form
const form = ref({
  url: "",
  file: null, // For torrent file
  fileName: "", // Display name for selected file
  series_name: "",
  season: "",
  episode_offset: "", // New
  total_seasons: "", // New
  save_path: "",
  category: "hoshino",
  tags: "", // Comma separated string
  is_paused: false,
  seeding_time: -1
});

let pollingInterval = null;

const stats = computed(() => ({
  total: tasks.value.length,
  downloading: tasks.value.filter(t => t.state === 'downloading' || t.state === 'stalledUP' || t.state === 'uploading' || t.state === 'metaDL').length,
  archived: tasks.value.filter(t => t.archived).length,
  failed: tasks.value.filter(t => t.archive_error || t.state === 'error').length,
}));

// Load Tasks
const loadTasks = async () => {
  try {
    tasks.value = await listDownloads();
  } catch (e) {
    console.error("Failed to load downloads:", e);
  }
};

const startPolling = () => {
  loadTasks();
  pollingInterval = setInterval(loadTasks, 2000);
};

const stopPolling = () => {
  if (pollingInterval) clearInterval(pollingInterval);
};

// File Selection
const handleFileChange = (event) => {
  const file = event.target.files[0];
  if (file) {
    if (!file.name.endsWith('.torrent')) {
        toast.error("请选择 .torrent 文件");
        return;
    }
    form.value.file = file;
    form.value.fileName = file.name;
    form.value.url = ""; // Clear magnet if file selected
  }
};

const triggerFileInput = () => {
    document.getElementById('torrent-file-input').click();
};

// Preview Logic
const handlePreview = async () => {
    if (inputType.value === 'magnet' && !form.value.url) return;
    if (inputType.value === 'file' && !form.value.file) return;

    previewing.value = true;
    
    try {
        const formData = new FormData();
        if (inputType.value === 'magnet') {
            formData.append('magnet', form.value.url);
        } else {
            formData.append('file', form.value.file);
        }

        const res = await previewTorrent(formData);
        
        previewFiles.value = res.files;
        previewHash.value = res.info_hash; // Store hash for potential reuse or just context
        showPreviewModal.value = true;
    } catch (e) {
        toast.error("预览失败: " + (e.response?.data?.detail || e.message));
    } finally {
        previewing.value = false;
    }
};

const cancelPreview = async () => {
    if (previewHash.value) {
        // Cleanup the temporary preview task
        try {
            await deleteTask(previewHash.value, true);
        } catch (e) {
            console.warn("Failed to clean up preview task", e);
        }
    }
    showPreviewModal.value = false;
    previewHash.value = "";
    previewFiles.value = [];
};

// Add Task
const addTask = async () => {

  if (inputType.value === 'magnet' && !form.value.url) return;
  if (inputType.value === 'file' && !form.value.file) return;

  loading.value = true;

  try {
    const payload = {
      url: form.value.url,
      save_path: form.value.save_path || undefined, 
      category: form.value.category,
      tags: form.value.tags ? form.value.tags.split(',').map(t => t.trim()) : [],
      is_paused: form.value.is_paused,
      seeding_time: parseInt(form.value.seeding_time),
      extra_vars: {}
    };

    if (form.value.series_name) payload.extra_vars.series_name = form.value.series_name;
    if (form.value.season) payload.extra_vars.season = parseInt(form.value.season);
    if (form.value.episode_offset) payload.extra_vars.episode_offset = parseInt(form.value.episode_offset);
    if (form.value.total_seasons) payload.extra_vars.total_seasons = parseInt(form.value.total_seasons);

     if (inputType.value === 'file') {
        // Construct FormData for file upload
        const formData = new FormData();
        formData.append('file', form.value.file);
        
        // Add other fields
        if (form.value.save_path) formData.append('save_path', form.value.save_path);
        formData.append('category', form.value.category);
        if (form.value.tags) formData.append('tags', form.value.tags);
        formData.append('is_paused', form.value.is_paused);
        formData.append('seeding_time', parseInt(form.value.seeding_time));

        // Add extra_vars as JSON string
        formData.append('extra_vars', JSON.stringify(payload.extra_vars));

        await addTorrentTask(formData);
    } else {
        await addMagnetTask(payload);
    }
    
    toast.success("任务添加成功");
    
    // Reset essential fields but keep some config maybe?
    form.value.url = ""; 
    form.value.series_name = "";
    // Close modal if open
    showPreviewModal.value = false;
    
    await loadTasks();
  } catch (e) {
    toast.error("添加失败: " + (e.response?.data?.detail || e.message));
  } finally {
    loading.value = false;
  }
};





// Retry Task
const handleRetry = async (task) => {
    try {
        await retryTask(task.info_hash);
        toast.success("重试请求已发送");
        await loadTasks();
    } catch (e) {
         toast.error("重试失败: " + (e.response?.data?.detail || e.message));
    }
};

// View Log
const viewLog = (task) => {
    currentLog.value = task.log || "暂无日志";
    showLogModal.value = true;
};

// Helpers
const getProgressColor = (progress) => {
  if (progress >= 1) return 'bg-emerald-500';
  return 'bg-cyan-500';
};

const formatSize = (bytes) => {
  if (bytes === undefined || bytes === null || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Confirm Dialog State
const showConfirm = ref(false);
const confirmConfig = ref({
  title: "确认操作",
  message: "",
  confirmText: "确认",
  action: null,
  isDelete: false // Extra flag for delete mode
});
const deleteFiles = ref(false);

const triggerDelete = (task) => {
    deleteFiles.value = false;
    confirmConfig.value = {
        title: "删除任务",
        message: `确定要删除任务 "${task.name}" 吗？`,
        confirmText: "确认删除",
        isDelete: true,
        action: async () => {
            try {
                await deleteTask(task.info_hash, deleteFiles.value);
                toast.success("任务已删除");
                await loadTasks();
            } catch (e) {
                toast.error("删除失败: " + (e.response?.data?.detail || e.message));
            }
        }
    };
    showConfirm.value = true;
};

const handleConfirmAction = async () => {
    if (confirmConfig.value.action) {
        await confirmConfig.value.action();
    }
    showConfirm.value = false;
};

onMounted(() => {
  startPolling();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<template>
  <div class="h-full flex flex-col gap-6 relative">
    <BaseConfirmDialog
      :show="showConfirm"
      :title="confirmConfig.title"
      :message="confirmConfig.message"
      :confirmText="confirmConfig.confirmText"
      @update:show="showConfirm = $event"
      @confirm="handleConfirmAction"
    >
        <div v-if="confirmConfig.isDelete" class="mt-4 flex items-center gap-2 p-3 bg-rose-50 dark:bg-rose-900/20 rounded-xl border border-rose-100 dark:border-rose-900/30">
            <input type="checkbox" id="delete-files" v-model="deleteFiles" class="rounded border-rose-300 text-rose-600 focus:ring-rose-500 w-4 h-4 cursor-pointer" />
            <label for="delete-files" class="text-sm font-bold text-rose-700 dark:text-rose-300 select-none cursor-pointer">
                同时删除本地文件 (无法撤销)
            </label>
        </div>
    </BaseConfirmDialog>

    <!-- 页面标题和统计 -->
    <div class="flex-shrink-0">
      <div class="flex items-end justify-between mb-2">
        <div class="flex items-center gap-3">
          <span class="w-2 h-10 bg-cyan-500 rounded-full shadow-lg shadow-cyan-500/30"></span>
          <div>
            <h1 class="text-4xl font-black text-slate-800 dark:text-white tracking-tight">下载管理</h1>
            <p class="text-xs font-bold text-slate-400 mt-1 uppercase tracking-widest">Download Manager</p>
          </div>
        </div>
        
        <!-- 统计卡片 -->
        <div class="flex gap-3">
          <div class="px-4 py-2 bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl rounded-2xl border border-white/60 dark:border-white/10 shadow-lg">
            <div class="text-xs font-bold text-slate-400 uppercase tracking-wider">总任务</div>
            <div class="text-2xl font-black text-slate-800 dark:text-white">{{ stats.total }}</div>
          </div>
          <div class="px-4 py-2 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 dark:from-blue-500/20 dark:to-cyan-500/20 backdrop-blur-xl rounded-2xl border border-blue-500/20 dark:border-blue-500/30 shadow-lg">
            <div class="text-xs font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">进行中</div>
            <div class="text-2xl font-black text-blue-600 dark:text-blue-400">{{ stats.downloading }}</div>
          </div>
          <div class="px-4 py-2 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 dark:from-emerald-500/20 dark:to-teal-500/20 backdrop-blur-xl rounded-2xl border border-emerald-500/20 dark:border-emerald-500/30 shadow-lg">
            <div class="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">已归档</div>
            <div class="text-2xl font-black text-emerald-600 dark:text-emerald-400">{{ stats.archived }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加任务区域 -->
    <div class="flex-shrink-0">
      <div class="bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2rem] p-6 border border-white/60 dark:border-white/10 shadow-xl">
        <div class="flex items-center justify-between mb-5">
          <div class="flex items-center gap-3">
            <div class="p-2.5 rounded-2xl bg-cyan-500 text-white shadow-lg shadow-cyan-500/30">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <div>
              <h2 class="text-lg font-black text-slate-900 dark:text-white tracking-tight">添加下载任务</h2>
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">New Download Task</p>
            </div>
          </div>
          
          <!-- Type Toggle -->
          <div class="flex bg-slate-100/50 dark:bg-slate-800/50 rounded-xl p-1.5 text-xs font-bold border border-slate-200/50 dark:border-white/5">
            <button 
              @click="inputType = 'magnet'"
              class="px-4 py-2 rounded-lg transition-all duration-300"
              :class="inputType === 'magnet' ? 'bg-white dark:bg-slate-600 shadow-lg text-cyan-600 dark:text-white' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'"
            >磁力链接</button>
            <button 
              @click="inputType = 'file'"
              class="px-4 py-2 rounded-lg transition-all duration-300"
              :class="inputType === 'file' ? 'bg-white dark:bg-slate-600 shadow-lg text-cyan-600 dark:text-white' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'"
            >种子文件</button>
          </div>
        </div>
        
        <div class="flex flex-col gap-4">
            <!-- Input Area -->
            <div class="flex gap-2">
                 <div v-if="inputType === 'magnet'" class="flex-1 relative">
                     <input
                      type="text"
                      v-model="form.url"
                      placeholder="粘贴磁力链接 (magnet:?...)"
                      class="block w-full rounded-xl border-0 bg-slate-50/50 dark:bg-black/20 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200/50 dark:ring-white/10 focus:ring-2 focus:ring-inset focus:ring-cyan-500 text-sm py-3 px-4 transition-all placeholder:text-slate-400 font-mono"
                    />
                 </div>
                 <div v-else class="flex-1 relative">
                     <input type="file" id="torrent-file-input" class="hidden" accept=".torrent" @change="handleFileChange">
                     <div 
                        @click="triggerFileInput"
                        class="block w-full rounded-xl border-0 bg-slate-50/50 dark:bg-black/20 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200/50 dark:ring-white/10 hover:bg-slate-100 dark:hover:bg-white/5 cursor-pointer text-sm py-3 px-4 transition-all flex items-center gap-2"
                     >
                        <span v-if="form.fileName" class="text-slate-900 dark:text-white font-mono truncate">{{ form.fileName }}</span>
                        <span v-else class="text-slate-400">点击选择 .torrent 文件...</span>
                     </div>
                 </div>

                 <button
                    @click="handlePreview"
                    :disabled="previewing"
                    class="px-5 py-2 rounded-xl font-bold text-sm text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 disabled:opacity-50 transition-all flex items-center gap-2"
                >
                    <svg v-if="previewing" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                    预览
                </button>
            </div>

            <!-- Metadata Inputs (Compact) -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <input type="text" v-model="form.series_name" placeholder="番剧名称 (可选)" class="compact-input" />
                <input type="number" v-model="form.season" placeholder="第几季 (S)" class="compact-input" />
                <input type="number" v-model="form.total_seasons" placeholder="总季数 (选填)" class="compact-input" />
                <input type="number" v-model="form.episode_offset" placeholder="集数偏移 (Offset)" class="compact-input" />
            </div>

            <!-- Advanced Options Toggle -->
            <div>
                <button @click="showAdvanced = !showAdvanced" class="text-xs font-bold text-slate-500 hover:text-cyan-600 flex items-center gap-1 transition-colors">
                    {{ showAdvanced ? '收起高级选项' : '展开高级选项' }}
                    <svg class="w-3 h-3 transition-transform" :class="{ 'rotate-180': showAdvanced }" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                </button>
                
                <div v-show="showAdvanced" class="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 p-3 bg-slate-50 dark:bg-black/20 rounded-xl animate-in slide-in-from-top-2 fade-in duration-200">
                    <input type="text" v-model="form.save_path" placeholder="保存路径 (可选)" class="compact-input bg-white dark:bg-slate-800" />
                    <input type="text" v-model="form.category" placeholder="分类 (默认 hoshino)" class="compact-input bg-white dark:bg-slate-800" />
                    <input type="text" v-model="form.tags" placeholder="标签 (逗号分隔)" class="compact-input bg-white dark:bg-slate-800" />
                    <div class="col-span-1 md:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-3">
                         <div class="flex flex-col gap-1">
                             <input type="number" v-model="form.seeding_time" placeholder="做种时间 (分钟, -1=默认, 0=不限制)" class="compact-input bg-white dark:bg-slate-800" />
                             <span class="text-[10px] text-slate-400 px-1">-1: 跟随全局设置, 0: 下载完立即停止</span>
                         </div>
                         <div class="flex items-center gap-2 px-1 h-10">
                            <input type="checkbox" id="pause-check" v-model="form.is_paused" class="rounded border-slate-300 text-cyan-600 focus:ring-cyan-500">
                            <label for="pause-check" class="text-xs font-bold text-slate-600 dark:text-slate-400">添加后暂停</label>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Add Button -->
            <button
                @click="addTask"
                :disabled="loading || (inputType==='magnet' && !form.url) || (inputType==='file' && !form.file)"
                class="w-full py-3 rounded-xl font-bold text-white shadow-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 active:scale-[0.99] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {{ loading ? "添加中..." : "立即添加任务" }}
            </button>
        </div>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="flex-1 bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2rem] border border-white/60 dark:border-white/10 shadow-xl overflow-hidden flex flex-col min-h-0">
        <div class="px-6 py-4 border-b border-slate-200/50 dark:border-white/10 flex items-center justify-between flex-shrink-0 bg-slate-50/50 dark:bg-slate-800/30">
            <div class="flex items-center gap-3">
              <div class="p-2 rounded-xl bg-slate-200 dark:bg-slate-700">
                <svg class="w-4 h-4 text-slate-600 dark:text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </div>
              <div>
                <h3 class="text-base font-black text-slate-900 dark:text-white tracking-tight">任务列表</h3>
                <p class="text-[10px] font-bold text-slate-400">共 {{ stats.total }} 个任务</p>
              </div>
            </div>
            <div class="flex gap-4 text-xs font-bold">
                 <div class="flex items-center gap-2">
                   <div class="w-2 h-2 rounded-full bg-blue-500 shadow-lg shadow-blue-500/50"></div>
                   <span class="text-blue-600 dark:text-blue-400">进行中 {{ stats.downloading }}</span>
                 </div>
                 <div class="flex items-center gap-2">
                   <div class="w-2 h-2 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50"></div>
                   <span class="text-emerald-600 dark:text-emerald-400">已归档 {{ stats.archived }}</span>
                 </div>
            </div>
        </div>

        <div class="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
            <div v-if="tasks.length === 0" class="flex flex-col items-center justify-center h-full text-slate-400 text-sm">
                <div class="w-20 h-20 rounded-[2rem] bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                  <svg class="w-10 h-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </div>
                <p class="font-bold text-slate-500 dark:text-slate-400">暂无下载任务</p>
                <p class="text-xs text-slate-400 mt-1">添加磁力链接或种子文件开始下载</p>
            </div>

            <div v-for="task in tasks" :key="task.info_hash" 
                 class="group bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-2xl p-5 border border-slate-100 dark:border-slate-700/50 hover:shadow-2xl hover:shadow-cyan-500/10 hover:-translate-y-1 transition-all duration-300">
                <div class="flex justify-between items-start mb-2">
                    <div class="min-w-0 flex-1 pr-4">
                        <h4 class="font-bold text-slate-800 dark:text-slate-200 truncate text-sm" :title="task.name">{{ task.name }}</h4>
                        <!-- Metadata Badges -->
                        <div class="flex flex-wrap gap-2 mt-1">
                            <span v-if="task.extra_vars?.series_name" class="badge bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">{{ task.extra_vars.series_name }}</span>
                             <span v-if="task.extra_vars?.season" class="badge bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300">S{{ task.extra_vars.season }}</span>
                             <span v-if="task.extra_vars?.total_seasons" class="badge bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300">共{{ task.extra_vars.total_seasons }}季</span>
                             <span v-if="task.extra_vars?.episode_offset" class="badge bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300">Offset: {{ task.extra_vars.episode_offset }}</span>
                        </div>
                    </div>
                    <div class="text-right flex-shrink-0">
                         <div class="text-xs font-mono text-slate-500 dark:text-slate-400">{{ formatSize(task.size) }}</div>
                         <div class="text-[10px] text-slate-400 mt-1 uppercase font-bold" 
                            :class="{'text-amber-500': task.state === 'pausedDL' || task.state === 'pausedUP'}">
                            {{ task.state }}
                         </div>
                    </div>
                </div>

                <!-- Progress Bar -->
                <div class="h-1.5 w-full bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden mb-2">
                    <div class="h-full transition-all duration-500" 
                         :class="getProgressColor(task.progress)"
                         :style="{ width: `${task.progress * 100}%` }"></div>
                </div>

                <div class="flex justify-between items-center text-xs">
                    <span class="text-slate-500 dark:text-slate-400 font-mono">{{ (task.progress * 100).toFixed(1) }}%</span>
                    
                    <!-- Archive Status -->
                    <div v-if="task.archived" class="flex items-center gap-2">
                        <div class="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-bold">
                            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                            已归档
                        </div>
                        <button 
                            @click="viewLog(task)"
                            class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 rounded text-slate-600 dark:text-slate-300 text-[10px] font-bold transition-colors"
                        >
                            日志
                        </button>
                        <button 
                            @click="triggerDelete(task)"
                            class="px-2 py-0.5 bg-rose-50 hover:bg-rose-100 dark:bg-rose-900/20 dark:hover:bg-rose-900/40 rounded text-rose-600 dark:text-rose-400 text-[10px] font-bold transition-colors"
                        >
                            删除
                        </button>
                    </div>
                    <div v-else-if="task.archive_error || task.state === 'error'" class="flex items-center gap-2">
                         <div class="flex items-center gap-1 text-rose-500 font-bold" :title="task.archive_error">
                            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                            {{ task.state === 'error' ? '下载错误' : '归档失败' }}
                        </div>
                        <button 
                            @click="viewLog(task)"
                            class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 rounded text-slate-600 dark:text-slate-300 text-[10px] font-bold transition-colors"
                        >
                            日志
                        </button>
                        <button 
                            @click="handleRetry(task)"
                            class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 rounded text-slate-600 dark:text-slate-300 text-[10px] font-bold transition-colors"
                        >
                            重试
                        </button>
                        <button 
                            @click="triggerDelete(task)"
                            class="px-2 py-0.5 bg-rose-50 hover:bg-rose-100 dark:bg-rose-900/20 dark:hover:bg-rose-900/40 rounded text-rose-600 dark:text-rose-400 text-[10px] font-bold transition-colors"
                        >
                            删除
                        </button>
                    </div>
                     <div v-else-if="task.state === 'metaDL' || task.progress < 1" class="flex items-center gap-2">
                         <div class="text-slate-400">下载中...</div>
                         <button 
                            @click="triggerDelete(task)"
                            class="px-2 py-0.5 bg-rose-50 hover:bg-rose-100 dark:bg-rose-900/20 dark:hover:bg-rose-900/40 rounded text-rose-600 dark:text-rose-400 text-[10px] font-bold transition-colors"
                        >
                            删除
                        </button>
                    </div>
                    <div v-else class="flex items-center gap-2">
                         <div class="text-cyan-600 dark:text-cyan-400 animate-pulse">处理中...</div>
                         <button 
                            @click="viewLog(task)"
                            class="px-2 py-0.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 rounded text-slate-600 dark:text-slate-300 text-[10px] font-bold transition-colors"
                        >
                            日志
                        </button>
                        <button 
                            @click="triggerDelete(task)"
                            class="px-2 py-0.5 bg-rose-50 hover:bg-rose-100 dark:bg-rose-900/20 dark:hover:bg-rose-900/40 rounded text-rose-600 dark:text-rose-400 text-[10px] font-bold transition-colors"
                        >
                            删除
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Preview Modal -->
    <div v-if="showPreviewModal" class="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm rounded-[2rem]">
        <div class="bg-white dark:bg-slate-900 w-full max-w-lg rounded-2xl shadow-2xl border border-slate-100 dark:border-white/10 flex flex-col max-h-[80%] animate-in zoom-in-95 duration-200">
            <div class="p-4 border-b border-slate-100 dark:border-white/10 flex justify-between items-center">
                <h3 class="font-bold text-lg text-slate-800 dark:text-white">文件列表预览</h3>
                <button @click="cancelPreview" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
            </div>
            <div class="p-4 overflow-y-auto custom-scrollbar flex-1">
                <ul class="space-y-2 text-sm">
                    <li v-for="(file, index) in previewFiles" :key="index" class="flex justify-between items-center py-2 px-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <span class="truncate pr-4 text-slate-700 dark:text-slate-300" :title="file.name">{{ file.name }}</span>
                        <span class="font-mono text-xs text-slate-500">{{ formatSize(file.size) }}</span>
                    </li>
                </ul>
            </div>
            <div class="p-4 border-t border-slate-100 dark:border-white/10 flex justify-end gap-2 bg-slate-50 dark:bg-slate-800/50 rounded-b-2xl">
                 <button @click="cancelPreview" class="px-4 py-2 text-slate-500 font-bold hover:text-slate-700 text-sm">关闭</button>
                 <button @click="addTask" :disabled="loading" class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-bold text-sm shadow-lg shadow-cyan-500/20">确认添加</button>
            </div>
        </div>
    </div>

    <!-- Log Modal -->
    <div v-if="showLogModal" class="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/20 backdrop-blur-sm rounded-[2rem]">
        <div class="bg-white dark:bg-slate-900 w-full max-w-2xl rounded-2xl shadow-2xl border border-slate-100 dark:border-white/10 flex flex-col max-h-[80%] animate-in zoom-in-95 duration-200">
            <div class="p-4 border-b border-slate-100 dark:border-white/10 flex justify-between items-center">
                <h3 class="font-bold text-lg text-slate-800 dark:text-white">任务执行日志</h3>
                <button @click="showLogModal = false" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
            </div>
            <div class="p-4 overflow-y-auto custom-scrollbar flex-1 bg-slate-50 dark:bg-black/20">
                <pre class="font-mono text-xs text-slate-600 dark:text-slate-300 whitespace-pre-wrap leading-relaxed">{{ currentLog }}</pre>
            </div>
            <div class="p-4 border-t border-slate-100 dark:border-white/10 flex justify-end gap-2 bg-slate-50 dark:bg-slate-800/50 rounded-b-2xl">
                 <button @click="showLogModal = false" class="px-4 py-2 text-slate-500 font-bold hover:text-slate-700 text-sm">关闭</button>
            </div>
        </div>
    </div>

  </div>
</template>

<style scoped>
.compact-input {
    @apply block w-full rounded-xl border-0 bg-slate-50/50 dark:bg-black/20 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200/50 dark:ring-white/10 focus:ring-2 focus:ring-inset focus:ring-cyan-500 text-sm py-2 px-3 transition-all placeholder:text-slate-400;
}
.badge {
    @apply inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium;
}
.slide-fade-enter-active { transition: all 0.3s ease-out; }
.slide-fade-leave-active { transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1); }
.slide-fade-enter-from, .slide-fade-leave-to { transform: translateY(-5px); opacity: 0; }

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(148, 163, 184, 0.3);
  border-radius: 20px;
}
</style>
