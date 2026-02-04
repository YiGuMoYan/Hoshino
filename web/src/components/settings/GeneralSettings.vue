<script setup>
import { ref, onMounted } from "vue";
import { getAppSettings, updateAppSettings } from "@/api/settings";

const appSettings = ref({
  language: "zh_CN",
  theme: "system",
  default_path: "",
  tmdb_api_key: "",
});
const loading = ref(false);

const saveAppSettings = async () => {
  loading.value = true;
  try {
    await updateAppSettings(appSettings.value);
    // You might want to use a global toast/notification here if available,
    // or emit an event to parent to show message
    // For now we will use a simple alert or console, or better:
    // we can pass a 'showMessage' prop or event.
    // Let's emit an event to keep it clean.
    emit("notify", { type: "success", text: "系统设置已保存" });
  } catch (e) {
    emit("notify", { type: "error", text: "保存失败: " + e.message });
  } finally {
    loading.value = false;
  }
};

const emit = defineEmits(["notify"]);

onMounted(async () => {
  try {
    const data = await getAppSettings();
    appSettings.value = data;
  } catch (e) {
    emit("notify", { type: "error", text: "加载设置失败" });
  }
});
</script>

<template>
  <div
    class="bg-white/60 dark:bg-[#1e293b]/60 backdrop-blur-md rounded-[2rem] shadow-sm border border-white/50 dark:border-white/5 p-10 h-full flex flex-col"
  >
    <div
      class="px-2 py-2 border-b border-slate-100/50 dark:border-white/5 mb-6"
    >
      <h3 class="text-xl font-bold text-slate-800 dark:text-white">常规设置</h3>
      <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
        系统级全局参数。
      </p>
    </div>

    <form @submit.prevent="saveAppSettings" class="space-y-6 max-w-2xl">
      <div class="group">
        <label
          class="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-2"
          >默认扫描路径</label
        >
        <input
          type="text"
          v-model="appSettings.default_path"
          class="block w-full rounded-2xl border-0 bg-slate-50/50 dark:bg-black/20 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-cyan-500 sm:text-base py-3.5 px-5 transition-all shadow-inner"
          placeholder="例如: D:\Anime"
        />
      </div>
      <div class="group">
        <label
          class="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-2"
          >系统语言</label
        >
        <select
          v-model="appSettings.language"
          class="block w-full rounded-2xl border-0 bg-slate-50/50 dark:bg-black/20 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-cyan-500 sm:text-base py-3.5 px-5 transition-all shadow-inner"
        >
          <option value="zh_CN">简体中文 (Chinese)</option>
          <option value="en_US">English</option>
        </select>
      </div>

      <div class="group">
        <label
          class="block text-sm font-bold text-slate-700 dark:text-slate-200 mb-2"
          >TMDB API 密钥</label
        >
        <input
          type="password"
          v-model="appSettings.tmdb_api_key"
          class="block w-full rounded-2xl border-0 bg-slate-50/50 dark:bg-black/20 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-cyan-500 sm:text-base py-3.5 px-5 transition-all shadow-inner"
          placeholder="从 themoviedb.org 获取"
        />
        <p class="mt-2 text-xs font-medium text-slate-400">
          用于搜索动漫元数据。在
          <a
            href="https://www.themoviedb.org/settings/api"
            target="_blank"
            class="text-cyan-500 hover:text-cyan-600"
            >TMDB 设置</a
          >
          获取 API 密钥。
        </p>
      </div>

      <div class="pt-8 flex justify-end">
        <button
          type="submit"
          :disabled="loading"
          class="inline-flex items-center px-8 py-3.5 border border-transparent font-bold rounded-2xl shadow-xl shadow-cyan-500/20 text-white bg-cyan-600 hover:bg-cyan-700 focus:outline-none disabled:opacity-50 transition-all active:scale-95"
        >
          <span v-if="loading">保存中...</span>
          <span v-else>保存设置</span>
        </button>
      </div>
    </form>
  </div>
</template>
