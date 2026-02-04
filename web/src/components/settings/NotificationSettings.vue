<script setup>
import { ref, onMounted } from "vue";
import { getSettingsByCategory, updateSettings, sendTestEmail } from "@/api/settings";
import BaseSelect from "@/components/core/BaseSelect.vue";

const settings = ref({
  "notification.email.enabled": "false",
  "notification.email.smtp_host": "",
  "notification.email.smtp_port": "587",
  "notification.email.smtp_user": "",
  "notification.email.smtp_pass": "",
  "notification.email.sender_name": "Hoshino Bot",
  "notification.email.receivers": "",
  
  "notification.enable_subscription_update": "true",
  "notification.enable_download_complete": "false",
  "notification.enable_archive_complete": "true",
  "notification.enable_manual_rename": "true",
});

const enableOptions = [
  { label: "开启", value: "true" },
  { label: "关闭", value: "false" },
];

const loading = ref(false);
const testing = ref(false);
const emit = defineEmits(["notify"]);

const loadSettings = async () => {
  try {
    const data = await getSettingsByCategory("notification");
    // data is array of objects { key: ..., value: ... }
    data.forEach(item => {
      settings.value[item.key] = item.value;
    });
  } catch (e) {
    emit("notify", { type: "error", text: "加载配置失败: " + e.message });
  }
};

const saveSettings = async () => {
  loading.value = true;
  try {
    await updateSettings(settings.value);
    emit("notify", { type: "success", text: "通知设置已保存" });
  } catch (e) {
    emit("notify", { type: "error", text: "保存失败: " + e.message });
  } finally {
    loading.value = false;
  }
};

const handleTestEmail = async () => {
    testing.value = true;
    try {
        // 先保存当前配置，以确保测试的是最新输入
        await updateSettings(settings.value);
        await sendTestEmail();
        emit("notify", { type: "success", text: "测试邮件已发送，请检查邮箱" });
    } catch (e) {
        emit("notify", { type: "error", text: "测试发送失败: " + e.message });
    } finally {
        testing.value = false;
    }
}

onMounted(() => {
  loadSettings();
});
</script>

<template>
  <div class="bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2.5rem] shadow-[0_20px_50px_-12px_rgba(0,0,0,0.1)] border border-white dark:border-white/10 overflow-hidden h-full flex flex-col relative">
    <!-- Header -->
    <div class="px-10 py-10 border-b border-slate-100 dark:border-white/5 bg-gradient-to-b from-white/50 to-transparent dark:from-white/5">
      <div class="flex items-center gap-4 mb-2">
        <div class="w-1.5 h-6 bg-amber-500 rounded-full shadow-[0_0_15px_rgba(245,158,11,0.5)]"></div>
        <h3 class="text-2xl font-black text-slate-800 dark:text-white tracking-tight">
          通知设置
        </h3>
      </div>
      <p class="text-sm font-bold text-slate-400 dark:text-slate-500 pl-5 uppercase tracking-wider">
        配置系统通知场景及其投递渠道
      </p>
    </div>

    <div class="px-10 py-10 overflow-y-auto custom-scrollbar flex-1">
      <form @submit.prevent="saveSettings" class="space-y-10 w-full">
        
        <!-- Main Toggle Card -->
        <div class="flex items-center justify-between p-8 bg-slate-100/50 dark:bg-white/5 rounded-[2.5rem] border border-white dark:border-white/5 shadow-inner group">
          <div class="flex items-center gap-5">
            <div class="p-4 bg-white dark:bg-slate-800 rounded-2xl shadow-sm text-amber-500 transition-transform group-hover:scale-110">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
               <label class="block text-base font-black text-slate-800 dark:text-white uppercase tracking-widest">启用邮件通知</label>
               <p class="text-xs font-bold text-slate-400 mt-1 uppercase tracking-tighter pl-0.5">Global Email Notification Switch</p>
            </div>
          </div>
          
          <div class="w-40">
            <BaseSelect
              v-model="settings['notification.email.enabled']"
              :options="enableOptions"
              class="rounded-2xl"
            />
          </div>
        </div>

        <!-- Conditional SMTP Config -->
        <transition name="fade">
          <div v-if="settings['notification.email.enabled'] === 'true'" class="space-y-10 animate-in fade-in slide-in-from-top-4 duration-500">
              
              <!-- SMTP Configuration Grid -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div class="group md:col-span-2">
                    <label class="block text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3 pl-1">SMTP Server Configuration</label>
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
                      <div class="md:col-span-3">
                        <input type="text" v-model="settings['notification.email.smtp_host']" placeholder="smtp.gmail.com" 
                            class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-amber-500 sm:text-base py-4 px-6 transition-all shadow-inner" />
                      </div>
                      <div>
                        <input type="number" v-model="settings['notification.email.smtp_port']" placeholder="587" 
                            class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-amber-500 sm:text-base py-4 px-6 transition-all shadow-inner" />
                      </div>
                    </div>
                  </div>
                  
                  <div class="group">
                    <label class="block text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3 pl-1">Account / User</label>
                    <input type="text" v-model="settings['notification.email.smtp_user']" placeholder="example@gmail.com" 
                        class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-amber-500 sm:text-base py-4 px-6 transition-all shadow-inner" />
                  </div>

                  <div class="group">
                    <label class="block text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3 pl-1">Password / App Key</label>
                    <input type="password" v-model="settings['notification.email.smtp_pass']" placeholder="***********" 
                        class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-amber-500 sm:text-base py-4 px-6 transition-all shadow-inner" />
                  </div>
                  
                  <div class="group">
                    <label class="block text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3 pl-1">Sender Identifier</label>
                    <input type="text" v-model="settings['notification.email.sender_name']" placeholder="Hoshino Bot" 
                        class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-amber-500 sm:text-base py-4 px-6 transition-all shadow-inner" />
                  </div>
                  
                  <div class="group">
                    <label class="block text-xs font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-3 pl-1">Recipient List (CSV)</label>
                    <input type="text" v-model="settings['notification.email.receivers']" placeholder="user@example.com" 
                        class="block w-full rounded-2xl border-0 bg-slate-50 dark:bg-white/5 text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-white/10 focus:ring-2 focus:ring-amber-500 sm:text-base py-4 px-6 transition-all shadow-inner" />
                  </div>
              </div>
              
              <div class="h-px bg-gradient-to-r from-transparent via-slate-200 dark:via-white/10 to-transparent my-4"></div>
              
              <!-- Scene Switches -->
              <div>
                <h4 class="text-xs font-black text-slate-400 dark:text-slate-500 mb-6 uppercase tracking-widest flex items-center gap-2">
                   <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                   </svg>
                   Notification Triggers
                </h4>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Scenario Item -->
                    <div v-for="(label, key) in {
                      'notification.enable_subscription_update': ['番剧订阅更新', '检测到新剧集并添加下载时通知'],
                      'notification.enable_archive_complete': ['归档任务完成', '番剧自动分类归档成功后通知'],
                      'notification.enable_manual_rename': ['需手动重命名', '自动归档失败或需要人工干预时通知'],
                      'notification.enable_download_complete': ['下载完成通知', '仅当下载完成且未触发归档时通知']
                    }" :key="key" 
                    class="flex items-center justify-between p-6 rounded-[1.8rem] bg-white dark:bg-white/5 border border-slate-100 dark:border-white/5 hover:border-amber-500/30 hover:shadow-lg transition-all duration-300 group">
                        <div class="pr-4">
                            <div class="text-sm font-black text-slate-700 dark:text-slate-200 uppercase tracking-widest">{{ label[0] }}</div>
                            <div class="text-[10px] font-bold text-slate-400 mt-1 uppercase tracking-tighter">{{ label[1] }}</div>
                        </div>
                         <div class="w-28 flex-shrink-0">
                           <BaseSelect
                             v-model="settings[key]"
                             :options="enableOptions"
                             class="rounded-xl"
                           />
                         </div>
                    </div>
                </div>
              </div>
          </div>
        </transition>

        <!-- Footer Actions -->
        <div class="pt-12 border-t border-slate-100 dark:border-white/5 flex flex-wrap items-center justify-between gap-6">
            <button 
              type="button" 
              @click="handleTestEmail"
              :disabled="testing || settings['notification.email.enabled'] !== 'true'"
              class="group flex items-center gap-2 text-xs font-black text-slate-400 hover:text-amber-500 disabled:opacity-30 transition-all uppercase tracking-widest"
            >
              <div class="p-2 bg-slate-100 dark:bg-white/5 rounded-lg group-hover:bg-amber-100 dark:group-hover:bg-amber-500/10 transition-colors">
                <svg v-if="testing" class="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </div>
              {{ testing ? "Sending..." : "Test SMTP Connection" }}
            </button>

          <button
            type="submit"
            :disabled="loading"
            class="flex items-center gap-3 px-12 py-4 font-black rounded-2xl shadow-2xl shadow-amber-500/30 text-white bg-slate-900 dark:bg-amber-500 hover:bg-slate-800 dark:hover:bg-amber-600 transition-all active:scale-95 disabled:opacity-50"
          >
            <svg v-if="loading" class="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span class="tracking-widest uppercase text-xs">{{ loading ? "Saving..." : "Commit Settings" }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
