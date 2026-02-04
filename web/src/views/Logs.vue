<script setup>
import { ref, onMounted, watch } from 'vue';
import { getLogs } from '@/api/logs';

const logs = ref([]);
const loading = ref(false);
const autoRefresh = ref(false);
let refreshInterval = null;

// Filters
const date = ref(new Date().toISOString().split('T')[0]);
const level = ref('');
const moduleFilter = ref('');

const levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG'];

const fetchLogs = async () => {
  loading.value = true;
  try {
    const params = {
      date: date.value,
      level: level.value || undefined,
      module: moduleFilter.value || undefined
    };
    logs.value = await getLogs(params);
  } catch (e) {
    console.error("Failed to fetch logs", e);
  } finally {
    loading.value = false;
  }
};

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value;
  if (autoRefresh.value) {
    refreshInterval = setInterval(fetchLogs, 5000);
  } else {
    clearInterval(refreshInterval);
  }
};

onMounted(() => {
  fetchLogs();
});

watch([date, level], () => {
  fetchLogs();
});

// Watch module filter with debounce could be added here, currently manual refresh or enter key
</script>

<template>
  <div class="h-full flex flex-col gap-6">
    <!-- 页面标题 -->
    <div class="flex-shrink-0">
      <div class="flex items-center gap-3 mb-2">
        <span class="w-2 h-10 bg-cyan-500 rounded-full shadow-lg shadow-cyan-500/30"></span>
        <div>
          <h1 class="text-4xl font-black text-slate-800 dark:text-white tracking-tight">系统日志</h1>
          <p class="text-xs font-bold text-slate-400 mt-1 uppercase tracking-widest">System Logs</p>
        </div>
      </div>
    </div>

    <!-- 筛选器栏 -->
    <div class="flex-shrink-0 bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2rem] p-5 border border-white/60 dark:border-white/10 shadow-xl">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="p-2.5 rounded-2xl bg-cyan-500 text-white shadow-lg shadow-cyan-500/30">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
          </div>
          <div>
            <h2 class="text-base font-black text-slate-900 dark:text-white tracking-tight">日志筛选</h2>
            <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Filter Options</p>
          </div>
        </div>
        
        <div class="flex items-center gap-3">
          <!-- Date Picker -->
          <input 
            type="date" 
            v-model="date"
            class="px-4 py-2.5 rounded-xl bg-slate-50/50 dark:bg-slate-800/50 border border-slate-200/50 dark:border-white/10 text-sm font-bold text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-cyan-500 transition-all"
          />
          
          <!-- Level Select -->
          <select 
            v-model="level"
            class="px-4 py-2.5 rounded-xl bg-slate-50/50 dark:bg-slate-800/50 border border-slate-200/50 dark:border-white/10 text-sm font-bold text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-cyan-500 transition-all"
          >
            <option value="">所有级别</option>
            <option v-for="l in levels" :key="l" :value="l">{{ l }}</option>
          </select>
          
          <!-- Module Filter -->
          <input 
            type="text" 
            v-model="moduleFilter"
            placeholder="过滤模块..."
            @keyup.enter="fetchLogs"
            class="px-4 py-2.5 rounded-xl bg-slate-50/50 dark:bg-slate-800/50 border border-slate-200/50 dark:border-white/10 text-sm font-bold text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-cyan-500 w-32 md:w-48 placeholder:text-slate-400 transition-all"
          />
          
          <button 
            @click="fetchLogs" 
            class="p-2.5 rounded-xl bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 hover:bg-cyan-500/20 transition-all shadow-lg hover:shadow-cyan-500/20"
            title="刷新"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          
          <button 
            @click="toggleAutoRefresh" 
            class="p-2.5 rounded-xl transition-all shadow-lg flex items-center gap-1"
            :class="autoRefresh ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 shadow-emerald-500/20' : 'bg-slate-100 dark:bg-slate-800 text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'"
            title="自动刷新"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 日志表格 -->
    <div class="flex-1 min-h-0 bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2rem] border border-white/60 dark:border-white/10 shadow-xl overflow-hidden flex flex-col">
      <!-- 表格标题 -->
      <div class="grid grid-cols-12 gap-4 px-6 py-4 border-b border-slate-200/50 dark:border-white/10 bg-slate-50/50 dark:bg-slate-800/30 text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">
        <div class="col-span-2">时间</div>
        <div class="col-span-1">级别</div>
        <div class="col-span-3">模块</div>
        <div class="col-span-6">消息</div>
      </div>
      
      <!-- 表格内容 -->
      <div class="flex-1 overflow-y-auto p-3 space-y-1.5">
        <div v-if="logs.length === 0" class="flex flex-col items-center justify-center h-full text-slate-400 text-sm">
          <div class="w-20 h-20 rounded-[2rem] bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
            <svg class="w-10 h-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <p class="font-bold text-slate-500 dark:text-slate-400">暂无日志</p>
          <p class="text-xs text-slate-400 mt-1">选择日期和筛选条件查看日志</p>
        </div>
        
        <div 
          v-for="(log, index) in logs" 
          :key="index"
          class="grid grid-cols-12 gap-4 px-5 py-3 rounded-xl hover:bg-white/60 dark:hover:bg-slate-800/60 transition-all duration-200 text-xs font-mono group"
        >
          <div class="col-span-2 text-slate-500 dark:text-slate-400 truncate font-bold" :title="log.timestamp">
             {{ new Date(log.timestamp).toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit', second:'2-digit', hour12: false}) }}
             <span class="text-[10px] text-slate-400 ml-1">{{ new Date(log.timestamp).getMilliseconds() }}ms</span>
          </div>
          
          <div class="col-span-1">
            <span 
              class="px-2 py-1 rounded-lg text-[10px] font-black uppercase tracking-wide"
              :class="{
                'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300': log.level === 'INFO',
                'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300': log.level === 'WARNING',
                'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300': log.level === 'ERROR',
                'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-300': log.level === 'DEBUG',
              }"
            >
              {{ log.level }}
            </span>
          </div>
          
          <div class="col-span-3 text-emerald-600 dark:text-emerald-400 truncate font-bold" :title="log.module">
            {{ log.module.split(':').slice(-2).join(':') }}
          </div>
          
          <div class="col-span-6 text-slate-700 dark:text-slate-300 break-words line-clamp-2" :title="log.message">
            {{ log.message }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Scrollbar styling */
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
