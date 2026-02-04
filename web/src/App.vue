<script setup>
import { useDark } from './composables/useDark'
import ToastContainer from './components/core/ToastContainer.vue'
const { isDark, toggleDark } = useDark()
</script>

<template>
  <div class="min-h-screen bg-[#f1f5f9] dark:bg-[#020617] flex font-sans transition-colors duration-500 overflow-hidden selection:bg-cyan-500 selection:text-white">
    <!-- Global Toast Container -->
    <ToastContainer />

    <!-- Aurora Background (Refined) -->
    <div class="fixed inset-0 z-0 pointer-events-none overflow-hidden">
        <div class="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-400/20 dark:bg-blue-600/10 rounded-full blur-[120px] animate-blob"></div>
        <div class="absolute top-[40%] right-[-10%] w-[40%] h-[40%] bg-cyan-300/20 dark:bg-cyan-500/10 rounded-full blur-[120px] animate-blob animation-delay-2000"></div>
        <div class="absolute bottom-[-10%] left-[20%] w-[40%] h-[40%] bg-violet-300/20 dark:bg-violet-600/10 rounded-full blur-[120px] animate-blob animation-delay-4000"></div>
    </div>

    <!-- Floating Navbar (Left) -->
    <aside class="fixed left-6 top-6 bottom-6 w-[88px] flex flex-col z-50">
       <!-- Glass Container -->
       <div class="w-full h-full bg-white/70 dark:bg-[#0f172a]/70 backdrop-blur-2xl border border-white/60 dark:border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.05)] rounded-[2rem] flex flex-col items-center py-8 transition-all duration-300">
          
          <!-- Logo -->
          <div class="w-12 h-12 mb-10 mx-auto">
             <img src="@/assets/logo.png" alt="Logo" class="w-full h-full object-contain drop-shadow-md hover:scale-110 transition-transform duration-300" />
          </div>

          <!-- Nav Items -->
          <nav class="flex-1 flex flex-col gap-4 w-full items-center">
            <router-link 
              to="/library" 
              class="relative w-12 h-12 flex items-center justify-center rounded-2xl transition-all duration-300 group"
              active-class="bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-md shadow-slate-900/20 dark:shadow-white/10"
              :class="[$route.path === '/library' ? '' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-white/5']"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
              <!-- Tooltip -->
              <div class="absolute left-16 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-xl translate-x-2 group-hover:translate-x-0">
                媒体库
              </div>
            </router-link>

            <router-link 
              to="/scan" 
              class="relative w-12 h-12 flex items-center justify-center rounded-2xl transition-all duration-300 group"
              active-class="bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-md shadow-slate-900/20 dark:shadow-white/10"
              :class="[$route.path === '/scan' ? '' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-white/5']"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <!-- Tooltip -->
              <div class="absolute left-16 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-xl translate-x-2 group-hover:translate-x-0">
                扫描
              </div>
            </router-link>

            <router-link 
              to="/download" 
              class="relative w-12 h-12 flex items-center justify-center rounded-2xl transition-all duration-300 group"
              active-class="bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-md shadow-slate-900/20 dark:shadow-white/10"
              :class="[$route.path === '/download' ? '' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-white/5']"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <!-- Tooltip -->
              <div class="absolute left-16 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-xl translate-x-2 group-hover:translate-x-0">
                下载
              </div>
            </router-link>

            <router-link 
              to="/subscription" 
              class="relative w-12 h-12 flex items-center justify-center rounded-2xl transition-all duration-300 group"
              active-class="bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-md shadow-slate-900/20 dark:shadow-white/10"
              :class="[$route.path === '/subscription' ? '' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-white/5']"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <!-- Tooltip -->
              <div class="absolute left-16 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-xl translate-x-2 group-hover:translate-x-0">
                订阅
              </div>
            </router-link>

            <router-link 
              to="/settings" 
              class="relative w-12 h-12 flex items-center justify-center rounded-2xl transition-all duration-300 group"
              active-class="bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-md shadow-slate-900/20 dark:shadow-white/10"
              :class="[$route.path === '/settings' ? '' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-white/5']"
            >
               <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <div class="absolute left-16 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-xl translate-x-2 group-hover:translate-x-0">
                配置
              </div>
            </router-link>

            <router-link 
              to="/logs" 
              class="relative w-12 h-12 flex items-center justify-center rounded-2xl transition-all duration-300 group"
              active-class="bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-md shadow-slate-900/20 dark:shadow-white/10"
              :class="[$route.path === '/logs' ? '' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-white/5']"
            >
               <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <div class="absolute left-16 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-xl translate-x-2 group-hover:translate-x-0">
                日志
              </div>
            </router-link>
          </nav>

          <!-- Action -->
          <div class="mt-auto">
            <button @click="toggleDark" class="relative w-12 h-12 flex items-center justify-center rounded-2xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 transition-all duration-300">
                <svg v-if="!isDark" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
            </button>
          </div>
       </div>
    </aside>

    <!-- Main Content (Shifted) -->
    <!-- Main Content (Shifted) -->
    <main class="fixed right-0 top-0 bottom-0 z-10 overflow-hidden" style="width: calc(100vw - 144px); height: 100vh;">
       <div class="w-full h-full p-8 overflow-y-auto">
          <router-view v-slot="{ Component }">
            <transition name="fade-slide" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
       </div>
    </main>
  </div>
</template>

<style>
/* Global Transitions */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.98);
}
</style>
