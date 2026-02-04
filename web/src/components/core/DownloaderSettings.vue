<script setup>
import { ref, onMounted } from "vue";
import { getSettingsByCategory, updateSettings } from "@/api/settings";
import { testConnection } from "@/api/downloads";
import { useToast } from "@/composables/useToast";

const toast = useToast();
const settings = ref([]);
const loading = ref(false);
const saving = ref(false);
const testing = ref(false);
// const message = ref({ type: "", text: "" }); // Removed

// Load settings
const loadSettings = async () => {
    loading.value = true;
    try {
        const data = await getSettingsByCategory("downloader");
        settings.value = data;
    } catch (e) {
        toast.error("加载配置失败: " + e.message);
    } finally {
        loading.value = false;
    }
};

// Save settings
const saveSettings = async () => {
    saving.value = true;
    try {
        const updates = {};
        for (const setting of settings.value) {
            updates[setting.key] = setting.value;
        }
        await updateSettings(updates);
        toast.success("配置已保存");
    } catch (e) {
        toast.error("保存失败: " + e.message);
    } finally {
        saving.value = false;
    }
};

// Test Connection
const handleTestConnection = async () => {
    testing.value = true;
    
    // Extract current values from form
    const host = settings.value.find(s => s.key === 'downloader.host')?.value;
    const username = settings.value.find(s => s.key === 'downloader.username')?.value;
    const password = settings.value.find(s => s.key === 'downloader.password')?.value;

    try {
        const res = await testConnection({ host, username, password });
        if (res.success) {
             toast.success("连接成功: " + res.message);
        } else {
             toast.error("连接失败: " + res.message);
        }
    } catch (e) {
        toast.error("测试出错: " + (e.response?.data?.detail || e.message));
    } finally {
        testing.value = false;
    }
};

onMounted(() => {
    loadSettings();
});
</script>

<template>
    <div class="bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2.5rem] shadow-[0_20px_50px_-12px_rgba(0,0,0,0.1)] border border-white dark:border-white/10 overflow-hidden h-full flex flex-col relative">
        <!-- Header -->
        <div class="px-10 py-10 border-b border-slate-100 dark:border-white/5 bg-gradient-to-b from-white/50 to-transparent dark:from-white/5">
            <div class="flex items-center gap-4 mb-2">
                <div class="w-1.5 h-6 bg-blue-500 rounded-full shadow-[0_0_15px_rgba(59,130,246,0.5)]"></div>
                <h3 class="text-2xl font-black text-slate-800 dark:text-white tracking-tight">
                    下载器配置
                </h3>
            </div>
            <p class="text-sm font-bold text-slate-400 dark:text-slate-500 pl-5 uppercase tracking-wider">
                配置 qBittorrent 连接信息与测试连通性
            </p>
        </div>

        <div class="px-12 py-10 overflow-y-auto custom-scrollbar flex-1">
            <div v-if="loading" class="flex flex-col items-center justify-center py-20 gap-4">
                <div class="relative w-12 h-12">
                    <div class="absolute inset-0 border-4 border-blue-500/20 rounded-full"></div>
                    <div class="absolute inset-0 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                </div>
                <p class="text-xs font-black text-slate-400 uppercase tracking-widest animate-pulse">Initializing...</p>
            </div>

            <div v-else-if="settings.length === 0" class="flex flex-col items-center justify-center py-20 text-center">
                 <div class="text-5xl mb-6">🔌</div>
                 <p class="text-sm font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-6">未找到下载器配置项</p>
                 <button @click="loadSettings" class="px-8 py-3 bg-slate-100 dark:bg-white/5 rounded-2xl text-xs font-black uppercase tracking-widest text-slate-600 dark:text-slate-300 hover:bg-blue-500 hover:text-white transition-all active:scale-95 shadow-lg shadow-slate-200/50 dark:shadow-none">
                    重新加载
                 </button>
            </div>

            <div v-else class="space-y-10 w-full">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
                    <div v-for="setting in settings" :key="setting.id" 
                        class="group relative"
                        :class="setting.key === 'downloader.host' ? 'md:col-span-2' : ''"
                    >
                        <!-- Field Header -->
                        <div class="flex items-center justify-between mb-3 pl-1">
                            <label class="block text-xs font-black text-slate-700 dark:text-slate-200 uppercase tracking-widest group-focus-within:text-blue-600 dark:group-focus-within:text-blue-400 transition-colors">
                                {{ setting.name }}
                            </label>
                            <span class="text-[9px] font-black text-slate-300 dark:text-slate-600 uppercase tracking-tighter bg-slate-50 dark:bg-white/5 px-2 py-0.5 rounded-md">
                                {{ setting.class_type }}
                            </span>
                        </div>

                        <!-- Input -->
                        <div class="relative">
                            <input 
                                v-if="setting.class_type !== 'boolean'"
                                :type="setting.class_type === 'password' ? 'password' : 'text'"
                                v-model="setting.value"
                                class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-blue-500 focus:bg-white dark:focus:bg-slate-800 sm:text-base py-4 px-6 transition-all duration-300 shadow-inner group-hover:ring-slate-300 dark:group-hover:ring-white/20"
                                :placeholder="setting.description"
                            />
                            
                            <!-- Icon Decorator -->
                            <div class="absolute inset-y-0 right-0 flex items-center pr-6 pointer-events-none text-slate-300 dark:text-slate-600 group-focus-within:text-blue-500 transition-colors">
                                <svg v-if="setting.key.includes('host')" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                                </svg>
                                <svg v-else-if="setting.key.includes('user')" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                                <svg v-else-if="setting.key.includes('pass')" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 00-2 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                </svg>
                            </div>
                        </div>

                        <!-- Help Text -->
                        <p v-if="setting.description" class="mt-3 pl-1 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-tighter flex items-center gap-1.5">
                            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {{ setting.description }}
                        </p>
                    </div>
                </div>

                <!-- Footer Actions -->
                <div class="pt-12 border-t border-slate-100 dark:border-white/5 flex flex-wrap items-center justify-between gap-6">
                    <button
                        @click="handleTestConnection"
                        :disabled="testing || saving"
                        class="group flex items-center gap-3 px-8 py-4 border-2 border-slate-200 dark:border-white/10 font-black rounded-2xl text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/50 hover:border-blue-500/30 hover:text-blue-500 transition-all active:scale-95 disabled:opacity-50"
                    >
                        <div class="relative">
                            <svg v-if="testing" class="animate-spin h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <svg v-else class="w-5 h-5 transition-transform group-hover:rotate-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071a9 9 0 0112.728 0M12 4v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707" />
                            </svg>
                        </div>
                        <span class="text-xs uppercase tracking-[0.2em]">{{ testing ? "Testing..." : "Test Connection" }}</span>
                    </button>

                    <button
                        @click="saveSettings"
                        :disabled="saving || testing"
                        class="flex items-center gap-3 px-12 py-4 font-black rounded-2xl shadow-2xl shadow-blue-500/30 text-white bg-slate-900 dark:bg-blue-600 hover:bg-slate-800 dark:hover:bg-blue-500 transition-all active:scale-95 disabled:opacity-50"
                    >
                        <svg v-if="saving" class="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span class="text-xs uppercase tracking-[0.2em]">{{ saving ? "Saving..." : "Commit Changes" }}</span>
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(148, 163, 184, 0.3);
  border-radius: 20px;
}
</style>
