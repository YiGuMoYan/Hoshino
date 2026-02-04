<script setup>
import { ref, onMounted } from "vue";
import {
  getSettingsByCategory,
  updateSettings,
  getPresets,
  createPreset,
  updatePreset,
  deletePreset as apiDeletePreset,
  testConnection,
} from "@/api/settings";
import BaseConfirmDialog from "@/components/core/BaseConfirmDialog.vue";
import { useToast } from "@/composables/useToast";

// In script setup
console.log('[LLMSettings] Component File Loaded (Hash Check)');

const toast = useToast();

// State
const llmConfig = ref({
  provider: "openai",
  api_key: "",
  base_url: "",
  model: "",
});

const loading = ref(false); // Restore specific state variables if needed or just remove if unused. 
// Actually previous code had loading and testing. I should restore them as they are used in template.
const testing = ref(false);

// Presets State
const presets = ref([]);
const selectedPresetId = ref("");
const showSavePreset = ref(false);
const newPresetName = ref("");

// Confirm Dialog State
const showConfirm = ref(false);
const confirmConfig = ref({
  title: "确认操作",
  message: "",
  confirmText: "确认",
  action: null,
});

const triggerConfirm = (msg, action) => {
  confirmConfig.value.message = msg;
  confirmConfig.value.action = action;
  showConfirm.value = true;
};

const handleConfirmAction = () => {
  if (confirmConfig.value.action) confirmConfig.value.action();
};

// Logic
const fetchPresets = async () => {
  try {
    const data = await getPresets();
    presets.value = data;
  } catch (e) {
    console.error("加载预设失败", e);
  }
};

const applyPreset = () => {
  if (!selectedPresetId.value) return;
  // Loose equality for ID
  const preset = presets.value.find((p) => p.id == selectedPresetId.value);
  if (preset) {
    llmConfig.value.base_url = preset.base_url;
    llmConfig.value.model = preset.model;
    if (preset.api_key) llmConfig.value.api_key = preset.api_key;
    toast.success(`已应用预设: ${preset.name}`);
  }
};

const handleUpdatePreset = async () => {
  if (!selectedPresetId.value) {
    showSavePreset.value = true;
    toast.info("当前未选择预设，请另存为新预设");
    return;
  }

  const preset = presets.value.find((p) => p.id == selectedPresetId.value);
  if (!preset) {
    toast.error("错误: 找不到选中的预设对象");
    return;
  }

  triggerConfirm(
    `确定要更新预设 "${preset.name}" 吗？此操作将覆盖原有配置。`,
    async () => {
      try {
        await updatePreset(preset.id, {
          name: preset.name,
          base_url: llmConfig.value.base_url,
          model: llmConfig.value.model,
          api_key: llmConfig.value.api_key,
        });
        toast.success("预设已更新");
        await fetchPresets();
      } catch (e) {
        toast.error("更新失败: " + (e.message || "未知错误"));
      }
    },
  );
};

const saveAsPreset = async () => {
  if (!newPresetName.value) return;
  try {
    await createPreset({
      name: newPresetName.value,
      base_url: llmConfig.value.base_url,
      model: llmConfig.value.model,
      api_key: llmConfig.value.api_key,
    });
    toast.success("预设保存成功");
    showSavePreset.value = false;
    newPresetName.value = "";
    await fetchPresets();
  } catch (e) {
    toast.error("保存失败: " + (e.message || "未知错误"));
  }
};

const deletePreset = async () => {
  if (!selectedPresetId.value) return;

  triggerConfirm("确定要删除此预设吗？此操作无法撤销。", async () => {
    try {
      await apiDeletePreset(selectedPresetId.value);
      toast.success("预设已删除");
      selectedPresetId.value = "";
      await fetchPresets();
    } catch (e) {
      toast.error("删除失败: " + e.message);
    }
  });
};

const testLLM = async () => {
  testing.value = true;
  toast.info("正在测试连接...");
  try {
    await testConnection(llmConfig.value);
    toast.success("连接测试成功！");
  } catch (e) {
    toast.error("连接测试失败: " + (e.message || "请检查网络或 Key"));
  } finally {
    testing.value = false;
  }
};

const applyLLMConfig = async () => {
  console.log('[LLMSettings] applyLLMConfig started');
  loading.value = true;

  try {
    const updates = {};
    for (const [key, value] of Object.entries(llmConfig.value)) {
      updates[`llm.${key}`] = value;
    }
    console.log('[LLMSettings] Sending updates:', updates);
    await updateSettings(updates);
    console.log('[LLMSettings] API success, calling toast.success');
    toast.success("大模型配置已应用");
  } catch (e) {
    console.error('[LLMSettings] API failed:', e);
    toast.error("应用失败: " + e.message);
  } finally {
    loading.value = false;
    console.log('[LLMSettings] applyLLMConfig finished');
  }
};

const debugToast = () => {
  console.log('[LLMSettings] Manual Test Toast Clicked');
  toast.success("测试提示框 (Test Toast) - " + Date.now());
};

onMounted(async () => {
  try {
    const llmSettings = await getSettingsByCategory("llm");
    llmSettings.forEach((setting) => {
      const key = setting.key.replace("llm.", "");
      // Only update if key exists in our config object to avoid pollution
      if (key in llmConfig.value) {
        llmConfig.value[key] = setting.value;
      }
    });
    fetchPresets();
  } catch (e) {
    toast.error("初始化失败: " + e.message);
  }
});
</script>

<template>
  <div
    class="bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2.5rem] shadow-[0_20px_50px_-12px_rgba(0,0,0,0.1)] border border-white dark:border-white/10 overflow-hidden h-full flex flex-col relative"
  >
    <!-- Confirm Dialog -->
    <BaseConfirmDialog
      :show="showConfirm"
      :message="confirmConfig.message"
      @update:show="showConfirm = $event"
      @confirm="handleConfirmAction"
    />

    <!-- Header -->
    <div class="px-10 py-10 border-b border-slate-100 dark:border-white/5 bg-gradient-to-b from-white/50 to-transparent dark:from-white/5">
      <div class="flex items-center gap-4 mb-2">
        <div class="w-1.5 h-6 bg-indigo-500 rounded-full shadow-[0_0_15px_rgba(99,102,241,0.5)]"></div>
        <h3 class="text-2xl font-black text-slate-800 dark:text-white tracking-tight">
          大模型配置 (LLM)
        </h3>
      </div>
      <p class="text-sm font-bold text-slate-400 dark:text-slate-500 pl-5 uppercase tracking-wider">
        管理 AI 模型的连接参数与环境预设
      </p>
    </div>

    <div class="px-10 py-10 overflow-y-auto custom-scrollbar flex-1">
      <!-- Presets Bar -->
      <div
        class="mb-12 p-8 bg-slate-100/50 dark:bg-white/5 rounded-[2.5rem] border border-white dark:border-white/5 shadow-inner"
      >
        <div
          class="flex flex-col md:flex-row md:items-center justify-between gap-8"
        >
          <div class="flex items-center gap-4">
            <div class="p-3 bg-white dark:bg-slate-800 rounded-2xl shadow-sm text-indigo-500">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <div>
              <h4
                class="text-sm font-black text-slate-800 dark:text-white tracking-widest uppercase mb-1"
              >
                快速预设 (Presets)
              </h4>
              <p class="text-xs font-bold text-slate-400 uppercase tracking-tighter">
                Quickly load saved configurations
              </p>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-4">
            <div class="relative group">
              <select
                v-model="selectedPresetId"
                @change="applyPreset"
                class="appearance-none pl-6 pr-12 py-3.5 rounded-2xl border-0 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-sm font-black shadow-sm ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-indigo-500 transition-all cursor-pointer group-hover:ring-slate-300 dark:group-hover:ring-white/20"
              >
                <option value="">-- 选择预设 --</option>
                <option
                  v-for="preset in presets"
                  :key="preset.id"
                  :value="preset.id"
                >
                  {{ preset.name }}
                </option>
              </select>
              <div
                class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-slate-400"
              >
                <svg
                  class="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </div>
            </div>

            <!-- Update/SaveAs/Delete Buttons Group -->
            <div
              class="flex items-center bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-white/10 p-1.5 shadow-sm"
            >
              <button
                @click="handleUpdatePreset"
                class="p-2.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-500/10 rounded-xl transition-all"
                :title="selectedPresetId ? '更新当前预设' : '另存为...'"
              >
                <svg
                  v-if="selectedPresetId"
                  class="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <svg
                  v-else
                  class="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                  />
                </svg>
              </button>
              <div class="w-px h-5 bg-slate-200 dark:bg-white/10 mx-2"></div>
              <button
                @click="deletePreset"
                :disabled="!selectedPresetId"
                class="p-2.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-500/10 rounded-xl transition-all disabled:opacity-30"
                title="删除当前预设"
              >
                <svg
                  class="w-5 h-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2.5"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Save Preset Dialog -->
        <transition name="fade">
          <div
            v-if="showSavePreset"
            class="mt-6 pt-6 border-t border-slate-200 dark:border-white/5 flex items-center gap-4 animate-in fade-in slide-in-from-top-2 duration-300"
          >
            <input
              type="text"
              v-model="newPresetName"
              placeholder="输入新预设名称 (例如: 我的 DeepSeek 配置)"
              class="flex-1 rounded-2xl border-0 bg-white dark:bg-slate-800 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-indigo-500 sm:text-base py-3.5 px-6 shadow-sm"
            />
            <button
              @click="saveAsPreset"
              :disabled="!newPresetName"
              class="px-8 py-3.5 bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-black rounded-2xl shadow-xl shadow-indigo-500/20 disabled:opacity-50 transition-all active:scale-95"
            >
              确认保存
            </button>
            <button
              @click="showSavePreset = false"
              class="px-6 py-3.5 text-sm font-black text-slate-500 hover:text-slate-700 dark:hover:text-white transition-colors"
            >
              取消
            </button>
          </div>
        </transition>
      </div>

      <form @submit.prevent="applyLLMConfig" class="space-y-10 w-full">
        <!-- Input Wrapper -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
          <!-- Base URL -->
          <div class="group md:col-span-2">
            <label
              class="block text-sm font-black text-slate-700 dark:text-slate-200 uppercase tracking-widest mb-3 group-focus-within:text-indigo-600 dark:group-focus-within:text-indigo-400 transition-colors"
              >OpenAI Base URL</label
            >
            <div class="relative">
              <input
                type="text"
                v-model="llmConfig.base_url"
                class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-indigo-500 sm:text-base py-4 px-6 transition-all duration-300 shadow-inner group-hover:ring-slate-300 dark:group-hover:ring-white/20"
                placeholder="https://api.openai.com/v1"
              />
              <div class="absolute inset-y-0 right-0 flex items-center pr-6 pointer-events-none text-slate-300 dark:text-slate-600">
                 <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" />
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.172 13.828a4 4 0 015.656 0l4 4a4 4 0 01-5.656 5.656l-1.101-1.102" />
                 </svg>
              </div>
            </div>
            <p class="mt-3 text-xs font-bold text-slate-400 uppercase tracking-widest pl-1">
              API Endpoint URL for the LLM Provider
            </p>
          </div>

          <!-- API Key -->
          <div class="group">
            <label
              class="block text-sm font-black text-slate-700 dark:text-slate-200 uppercase tracking-widest mb-3 group-focus-within:text-indigo-600 dark:group-focus-within:text-indigo-400 transition-colors"
              >API Key</label
            >
            <div class="relative">
              <input
                type="password"
                v-model="llmConfig.api_key"
                class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-indigo-500 sm:text-base py-4 px-6 transition-all duration-300 shadow-inner group-hover:ring-slate-300 dark:group-hover:ring-white/20"
                placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
              />
              <div class="absolute inset-y-0 right-0 flex items-center pr-6 pointer-events-none text-slate-300 dark:text-slate-600">
                 <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                 </svg>
              </div>
            </div>
          </div>

          <!-- Model -->
          <div class="group">
            <label
              class="block text-sm font-black text-slate-700 dark:text-slate-200 uppercase tracking-widest mb-3 group-focus-within:text-indigo-600 dark:group-focus-within:text-indigo-400 transition-colors"
              >模型名称 (Model)</label
            >
            <div class="relative">
              <input
                type="text"
                v-model="llmConfig.model"
                class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-indigo-500 sm:text-base py-4 px-6 transition-all duration-300 shadow-inner group-hover:ring-slate-300 dark:group-hover:ring-white/20"
                placeholder="gpt-4 / deepseek-chat"
              />
              <div class="absolute inset-y-0 right-0 flex items-center pr-6 pointer-events-none text-slate-300 dark:text-slate-600">
                 <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                 </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer Actions -->
        <div
          class="pt-12 border-t border-slate-100 dark:border-white/5 flex flex-wrap items-center justify-between gap-6"
        >
          <div class="flex items-center gap-4">
            <!-- Debug Toast Button -->
            <button
               type="button"
               @click="debugToast"
               class="inline-flex items-center px-6 py-4 border-2 border-dashed border-slate-200 dark:border-white/10 text-slate-400 rounded-2xl hover:bg-slate-50 dark:hover:bg-white/5 transition-all font-black text-xs uppercase tracking-widest active:scale-95"
            >
              🛠️ 测试弹窗
            </button>
          </div>

          <div class="flex items-center gap-4">
            <!-- Test Connection -->
            <button
              type="button"
              @click="testLLM"
              :disabled="testing || loading"
              class="inline-flex items-center px-10 py-4 border-2 border-slate-200 dark:border-white/10 font-black rounded-2xl text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/50 focus:outline-none transition-all active:scale-95 disabled:opacity-50"
            >
              <svg v-if="testing" class="animate-spin -ml-1 mr-3 h-5 w-5 text-indigo-500" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span class="tracking-widest uppercase text-xs">{{ testing ? "测试中..." : "测试连接" }}</span>
            </button>

            <!-- Apply Config -->
            <button
              type="submit"
              :disabled="loading || testing"
              class="inline-flex items-center px-10 py-4 font-black rounded-2xl shadow-2xl shadow-indigo-500/30 text-white bg-slate-900 dark:bg-indigo-500 hover:bg-slate-800 dark:hover:bg-indigo-600 transition-all active:scale-95 disabled:opacity-50"
            >
              <svg v-if="loading" class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span class="tracking-widest uppercase text-xs">{{ loading ? "保存中..." : "保存环境配置" }}</span>
            </button>
          </div>
        </div>
      </form>
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
