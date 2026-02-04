<script setup>
import { ref, watch, onMounted } from "vue";
import { getSettingsByCategory, updateSettings } from "@/api/settings";
import BaseSelect from "@/components/core/BaseSelect.vue";
import { useToast } from "@/composables/useToast";

const props = defineProps({
  category: {
    type: String,
    required: true,
  },
  title: {
    type: String,
    default: "",
  },
  description: {
    type: String,
    default: "",
  },
});

const toast = useToast();
// const emit = defineEmits(["notify"]); // Removed in favor of global toast

const settings = ref([]);
const loading = ref(false);
const formData = ref({});

const fetchSettings = async () => {
  try {
    const data = await getSettingsByCategory(props.category);
    settings.value = data;

    // Initialize form data
    data.forEach((setting) => {
      formData.value[setting.key] = setting.value;
    });
  } catch (e) {
    toast.error("加载设置失败: " + e.message);
  }
};

const saveSettings = async () => {
  loading.value = true;
  try {
    await updateSettings(formData.value);
    toast.success("设置已保存");
  } catch (e) {
    toast.error("保存失败: " + e.message);
  } finally {
    loading.value = false;
  }
};

const normalizeOptions = (options) => {
  if (!Array.isArray(options)) return [];
  return options.map((opt) => {
    if (typeof opt === "object" && opt !== null) return opt;
    // Special case for boolean strings from backend if needed, or just display as is
    // Backend sends "true"/"false" strings for boolean options currently.
    // If we want localized, we map here? 
    // "true" -> "开启", "false" -> "关闭"
    if (opt === "true") return { label: "开启", value: "true" };
    if (opt === "false") return { label: "关闭", value: "false" };
    
    return { label: opt, value: opt };
  });
};

onMounted(() => {
  fetchSettings();
});
</script>

<template>
  <div
    class="bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2.5rem] shadow-[0_20px_50px_-12px_rgba(0,0,0,0.1)] border border-white dark:border-white/10 overflow-hidden h-full flex flex-col relative"
  >
    <!-- Header -->
    <div class="px-10 py-10 border-b border-slate-100 dark:border-white/5 bg-gradient-to-b from-white/50 to-transparent dark:from-white/5">
      <div class="flex items-center gap-4 mb-2">
        <div class="w-1.5 h-6 bg-cyan-500 rounded-full shadow-[0_0_15px_rgba(6,182,212,0.5)]"></div>
        <h3 class="text-2xl font-black text-slate-800 dark:text-white tracking-tight">
          {{ title || category }}
        </h3>
      </div>
      <p class="text-sm font-bold text-slate-400 dark:text-slate-500 pl-5 uppercase tracking-wider">
        {{ description }}
      </p>
    </div>

    <!-- Scrollable Content -->
    <div class="px-12 py-10 overflow-y-auto custom-scrollbar flex-1">
      <form @submit.prevent="saveSettings" class="space-y-10 w-full">
        <div v-for="setting in settings" :key="setting.key" class="group relative">
          <!-- Field Header -->
          <div class="flex items-center justify-between mb-3">
            <label
              class="block text-sm font-black text-slate-700 dark:text-slate-200 uppercase tracking-widest transition-colors group-focus-within:text-cyan-600 dark:group-focus-within:text-cyan-400"
            >
              {{ setting.name }}
            </label>
            <span v-if="setting.class_type" class="text-[10px] font-black text-slate-300 dark:text-slate-600 uppercase tracking-tighter bg-slate-100 dark:bg-white/5 px-2 py-0.5 rounded-md">
              {{ setting.class_type }}
            </span>
          </div>

          <!-- Text/Password/Number Input -->
          <div v-if="['text', 'password', 'number'].includes(setting.class_type)" class="relative">
            <input
              :type="setting.class_type"
              v-model="formData[setting.key]"
              class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-cyan-500 focus:bg-white dark:focus:bg-slate-800 sm:text-base py-4 px-6 transition-all duration-300 shadow-inner group-hover:ring-slate-300 dark:group-hover:ring-white/20"
              :placeholder="setting.description"
            />
            <div class="absolute inset-y-0 right-0 flex items-center pr-4 pointer-events-none opacity-0 group-focus-within:opacity-100 transition-opacity">
              <svg class="w-5 h-5 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
          </div>

          <!-- Select Input -->
          <div v-else-if="setting.class_type === 'select'" class="relative">
             <BaseSelect
              v-model="formData[setting.key]"
              :options="normalizeOptions(setting.options)"
              :placeholder="setting.description || '请选择'"
              class="rounded-2xl"
            />
          </div>

          <!-- Textarea -->
          <div v-else-if="setting.class_type === 'textarea'" class="relative">
            <textarea
              v-model="formData[setting.key]"
              rows="4"
              class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-cyan-500 focus:bg-white dark:focus:bg-slate-800 sm:text-base py-4 px-6 transition-all duration-300 shadow-inner group-hover:ring-slate-300 dark:group-hover:ring-white/20"
              :placeholder="setting.description"
            ></textarea>
          </div>

          <!-- Help Text -->
          <p
            v-if="setting.description"
            class="mt-3 text-xs font-bold text-slate-400 dark:text-slate-500 flex items-center gap-1.5 pl-1"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span v-html="setting.description"></span>
          </p>
        </div>

        <!-- Submit Button Area -->
        <div class="pt-10 flex justify-end">
          <button
            type="submit"
            :disabled="loading"
            class="group relative inline-flex items-center justify-center px-10 py-4 font-black rounded-2xl overflow-hidden transition-all duration-300"
            :class="[
              loading 
                ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                : 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:scale-[1.02] active:scale-[0.98] shadow-2xl shadow-slate-500/20'
            ]"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-cyan-500 to-blue-500 opacity-0 group-hover:opacity-10 dark:group-hover:opacity-5 transition-opacity"></div>
            <span class="relative flex items-center gap-2">
              <svg v-if="loading" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ loading ? "正在保存..." : "同步配置" }}
              <svg v-if="!loading" class="w-5 h-5 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M17 8l4 4m0 0l-4 4m4-4H3" />
              </svg>
            </span>
          </button>
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
