<script setup>
import { ref, onMounted } from "vue";
import { getAllSettings, getSettingsByCategory } from "@/api/settings";
import DynamicSettingsForm from "@/components/settings/DynamicSettingsForm.vue";
import BaseConfirmDialog from "@/components/core/BaseConfirmDialog.vue";
import LLMSettings from "@/components/settings/LLMSettings.vue";
import DownloaderSettings from "@/components/core/DownloaderSettings.vue";
import NotificationSettings from "@/components/settings/NotificationSettings.vue";


// Navigation State
const activeSection = ref("about");
const settingsCategories = ref([]);
const menuItems = ref([
  { id: "llm", label: "大模型配置", icon: "M13 10V3L4 14h7v7l9-11h-7z" },
  {
    id: "about",
    label: "关于系统",
    icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  },
]);

// Category name mapping
const categoryNames = {
  app: "应用设置",
  tmdb: "TMDB 配置",
  llm: "LLM 配置",
  downloader: "下载器配置",
  notification: "通知设置",
};

const categoryIcons = {
  app: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-1.066 2.573c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z",
  tmdb: "M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z",
  downloader: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4",
};

// App Settings State
const appSettings = ref({
  language: "zh_CN",
  theme: "system",
});

const loading = ref(false);
const message = ref({ type: "", text: "" });

// Confirm Dialog State (Keep for potential other usages, though currently only LLM used it)
// We might want to keep it generic if other dynamic settings need it?
// For now, let's keep it simple.
const showConfirmDialog = ref(false);
const confirmMessage = ref("");
const confirmAction = ref(null);

const handleConfirm = () => {
  if (confirmAction.value) confirmAction.value();
  showConfirmDialog.value = false;
};

// Fetch settings categories and build menu
const fetchSettingsCategories = async () => {
  try {
    const allSettings = await getAllSettings();
    const categories = Object.keys(allSettings).filter((cat) => cat !== "llm" && cat !== "downloader" && cat !== "notification");

    // Build menu items from categories
    const dynamicMenuItems = categories.map((cat) => ({
      id: cat,
      label: categoryNames[cat] || cat,
      icon:
        categoryIcons[cat] ||
        "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-1.066 2.573c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z",
    }));

    // Prepend dynamic items before LLM and About
    menuItems.value = [
      ...dynamicMenuItems,
      { id: "downloader", label: "下载器配置", icon: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" },
      { id: "notification", label: "通知设置", icon: "M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" },
      { id: "llm", label: "大模型配置", icon: "M13 10V3L4 14h7v7l9-11h-7z" },

      {
        id: "about",
        label: "关于系统",
        icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
      },
    ];

    settingsCategories.value = categories;
  } catch (e) {
    console.error("Failed to fetch settings categories:", e);
  }
};

const handleNotify = (notification) => {
  message.value = notification;
};

onMounted(async () => {
  try {
    // Fetch settings categories first
    await fetchSettingsCategories();
  } catch (e) {
    message.value = { type: "error", text: "初始化失败: " + e.message };
  }
});
</script>

<template>
  <div class="h-full flex flex-col md:flex-row gap-8 relative">
    <!-- Custom Confirm Dialog -->
    <!-- Custom Confirm Dialog -->
    <BaseConfirmDialog
      :show="showConfirmDialog"
      :message="confirmMessage"
      @update:show="showConfirmDialog = $event"
      @confirm="handleConfirm"
      title="🔥 确认操作"
      confirm-text="确认执行"
    />
    <!-- Settings Sidebar -->
    <div class="w-full md:w-72 flex-shrink-0">
      <div class="px-2 mb-8">
        <h2 class="text-3xl font-black text-slate-800 dark:text-white tracking-tight flex items-center gap-3">
          <span class="w-2 h-8 bg-cyan-500 rounded-full"></span>
          系统设置
        </h2>
        <p class="text-xs font-bold text-slate-400 mt-2 uppercase tracking-widest pl-5">System Configuration</p>
      </div>

      <div class="flex flex-col gap-2.5 p-2 bg-slate-100/50 dark:bg-white/5 rounded-[2.5rem] border border-white dark:border-white/5 shadow-inner">
        <button
          v-for="item in menuItems"
          :key="item.id"
          @click="activeSection = item.id"
          class="flex items-center px-4 py-3.5 rounded-[1.8rem] text-sm font-bold transition-all duration-500 relative overflow-hidden group"
          :class="[
            activeSection === item.id
              ? 'bg-white dark:bg-slate-800 text-cyan-600 dark:text-white shadow-[0_10px_20px_-5px_rgba(0,0,0,0.1)] dark:shadow-none'
              : 'text-slate-500 dark:text-slate-400 hover:bg-white/60 dark:hover:bg-white/5 hover:text-slate-700 dark:hover:text-slate-200',
          ]"
        >
          <!-- Active Background Glow -->
          <div 
            v-if="activeSection === item.id"
            class="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-transparent pointer-events-none"
          ></div>

          <div
            class="p-2.5 rounded-2xl mr-3.5 transition-all duration-500 z-10"
            :class="[
              activeSection === item.id
                ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30 rotate-3'
                : 'bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400 group-hover:bg-slate-300 dark:group-hover:bg-slate-600 group-hover:text-slate-700 dark:group-hover:text-white',
            ]"
          >
            <svg
              class="w-5 h-5 transition-transform duration-500 group-hover:scale-110"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2.5"
                :d="item.icon"
              />
            </svg>
          </div>
          <span class="z-10 tracking-wide transition-colors duration-300">{{ item.label }}</span>
          
          <!-- Indicator Dot -->
          <div 
            v-if="activeSection === item.id"
            class="ml-auto w-1.5 h-1.5 bg-cyan-500 rounded-full shadow-[0_0_10px_rgba(6,182,212,0.8)] z-10"
          ></div>
        </button>
      </div>
    </div>

    <!-- Content Area -->
    <div class="flex-1 min-w-0">
      <!-- LLM CONFIGURATION SECTION -->
      <LLMSettings
        v-if="activeSection === 'llm'"
        key="llm"
        @notify="handleNotify"
      />

      <DownloaderSettings
        v-if="activeSection === 'downloader'"
        key="downloader"
      />

      <NotificationSettings
        v-if="activeSection === 'notification'"
        key="notification"
        @notify="handleNotify"
      />


      <!-- DYNAMIC SETTINGS SECTIONS (app, tmdb, etc.) -->
      <DynamicSettingsForm
        v-if="settingsCategories.includes(activeSection)"
        :key="activeSection"
        :category="activeSection"
        :title="categoryNames[activeSection] || activeSection"
        :description="`管理 ${categoryNames[activeSection] || activeSection} 相关配置`"
        @notify="handleNotify"
      />

      <!-- ABOUT -->
      <div
        v-show="activeSection === 'about'"
        key="about"
        class="bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2.5rem] shadow-[0_20px_50px_-12px_rgba(0,0,0,0.1)] border border-white dark:border-white/10 p-12 h-full flex items-center justify-center text-center overflow-hidden relative"
      >
        <!-- Background Decorative Elements -->
        <div class="absolute -top-24 -right-24 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -bottom-24 -left-24 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div class="w-full max-w-2xl px-6 relative z-10">
          <!-- Logo & Header -->
          <div class="mb-12">
            <div
              class="relative w-32 h-32 mx-auto mb-8 transition-all duration-700 animate-float"
            >
              <div class="absolute inset-0 bg-cyan-500/20 rounded-full blur-2xl animate-pulse"></div>
              <img src="@/assets/logo.png" alt="Hoshino Logo" class="relative w-full h-full object-contain drop-shadow-2xl" />
            </div>
            
            <h3
              class="text-5xl font-black text-slate-800 dark:text-white tracking-tighter mb-4"
            >
              Hoshino
            </h3>
            
            <div class="flex items-center justify-center gap-3">
              <span
                class="px-4 py-1.5 bg-slate-100 dark:bg-white/10 rounded-full text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-400 border border-white dark:border-white/5 shadow-sm"
                >Alpha v0.1.0</span
              >
              <div class="w-1.5 h-1.5 bg-slate-300 dark:bg-slate-600 rounded-full"></div>
              <span
                class="px-4 py-1.5 bg-cyan-500/10 dark:bg-cyan-500/20 rounded-full text-[10px] font-black uppercase tracking-widest text-cyan-600 dark:text-cyan-400 border border-cyan-500/20 shadow-sm"
                >Ether UI Engine</span
              >
            </div>
          </div>

          <!-- Slogan -->
          <p
            class="text-xl text-slate-600 dark:text-slate-400 font-bold mb-14 leading-relaxed tracking-tight"
          >
            A next-generation Intelligent Media Management Center<br />
            <span class="text-slate-400 dark:text-slate-500 font-medium text-lg">专为动漫爱好者打造的智能管理中心</span>
          </p>

          <!-- Feature Grid -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
            <div
              v-for="feature in [
                { emoji: '🧠', title: 'LLM 驱动', desc: '智能重命名与整理', color: 'indigo' },
                { emoji: '🎬', title: '自动刮削', desc: '双源元数据聚合', color: 'cyan' },
                { emoji: '⚡', title: '极速体验', desc: '现代化流体交互', color: 'amber' }
              ]"
              :key="feature.title"
              class="group/card p-6 bg-white dark:bg-white/5 rounded-[2rem] border border-slate-100 dark:border-white/5 shadow-sm hover:shadow-2xl hover:border-cyan-500/30 hover:-translate-y-2 transition-all duration-500"
            >
              <div class="text-4xl mb-4 transition-transform duration-500 group-hover/card:scale-125 group-hover/card:rotate-6">{{ feature.emoji }}</div>
              <div class="font-black text-slate-800 dark:text-white text-sm mb-1 uppercase tracking-widest">
                {{ feature.title }}
              </div>
              <div class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-tighter">
                {{ feature.desc }}
              </div>
            </div>
          </div>

          <!-- Tech Badges -->
          <div class="flex flex-wrap justify-center items-center gap-4 mb-16 px-4">
            <span
              v-for="tech in ['Vue 3', 'FastAPI', 'Python', 'Tailwind']"
              :key="tech"
              class="px-3 py-1 text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-slate-600 border-b-2 border-slate-100 dark:border-white/5 hover:text-cyan-500 hover:border-cyan-500/50 transition-all cursor-default"
              >{{ tech }}</span
            >
          </div>

          <!-- Footer -->
          <div class="pt-8 border-t border-slate-100 dark:border-white/5">
            <div class="text-[10px] font-black text-slate-400 dark:text-slate-700 uppercase tracking-[0.3em]">
              Build 2026.02.04 · Made with ❤️ for ACG
            </div>
          </div>
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

@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0); }
  50% { transform: translateY(-20px) rotate(2deg); }
}

.animate-float {
  animation: float 6s ease-in-out infinite;
}
</style>
