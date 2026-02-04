<template>
  <div class="space-y-6">
    <!-- 头部区域 -->
    <div class="flex-shrink-0 flex flex-col gap-6">
      
      <!-- 标题栏 -->
      <div class="flex items-end justify-between px-1">
          <div class="flex items-center gap-3">
            <span class="w-2 h-10 bg-cyan-500 rounded-full shadow-lg shadow-cyan-500/30"></span>
            <div>
              <h1 class="text-4xl font-black text-slate-800 dark:text-white tracking-tight">媒体库</h1>
              <p class="text-xs font-bold text-slate-400 mt-1 uppercase tracking-widest">Media Library · {{ items.length }} Items</p>
            </div>
          </div>

          <button
            @click="startScan"
            class="group flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl border border-white/60 dark:border-white/10 shadow-lg hover:shadow-cyan-500/20 hover:border-cyan-500/30 transition-all active:scale-95"
            :disabled="loading"
          >
             <div :class="loading ? 'animate-spin text-cyan-500' : 'text-slate-500 dark:text-slate-400 group-hover:text-cyan-500'">
               <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path v-if="loading" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                 <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
               </svg>
             </div>
             <span class="text-sm font-bold text-slate-600 dark:text-slate-300 group-hover:text-cyan-600 dark:group-hover:text-cyan-400">
               {{ loading ? "同步中..." : "刷新库" }}
             </span>
          </button>
      </div>

      <!-- 筛选工具栏 -->
      <div class="bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2rem] p-3 border border-white/60 dark:border-white/10 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          
          <!-- 主要标签页 -->
          <div class="flex p-1 bg-slate-100/50 dark:bg-black/20 rounded-2xl overflow-x-auto scrollbar-hide">
              <button 
                  v-for="tab in [
                    { id: 'all', label: '全部' },
                    { id: 'current', label: '连载中' },
                    { id: 'ended', label: '完结' },
                    { id: 'subscribed', label: '我的订阅' }
                  ]"
                  :key="tab.id"
                  @click="setMainFilter(tab.id)"
                  class="px-5 py-2.5 rounded-xl text-sm font-bold transition-all duration-300 relative overflow-hidden whitespace-nowrap"
                  :class="activeTab === tab.id ? 'bg-white dark:bg-slate-700 text-cyan-600 dark:text-cyan-400 shadow-md' : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200'"
              >
                 {{ tab.label }}
                 <div v-if="activeTab === tab.id" class="absolute bottom-0 left-4 right-4 h-0.5 bg-cyan-500 rounded-full"></div>
              </button>
          </div>

          <!-- 右侧过滤器 -->
          <div class="flex items-center gap-4 px-2 overflow-x-auto scrollbar-hide pb-1 lg:pb-0">
              <!-- 星期选择 -->
              <div class="flex items-center gap-1.5">
                 <button 
                   v-for="(d, i) in ['一','二','三','四','五','六','日']" 
                   :key="i"
                   @click="filterDay = filterDay === i ? 'all' : i"
                   class="w-9 h-9 flex items-center justify-center rounded-xl text-xs font-bold transition-all duration-200 border"
                   :class="filterDay === i ? 'bg-cyan-500 border-cyan-500 text-white shadow-lg shadow-cyan-500/30 scale-110' : 'bg-transparent border-transparent text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-600'"
                 >
                   {{ d }}
                 </button>
              </div>
              
              <div class="w-px h-8 bg-slate-200 dark:bg-white/10 mx-2"></div>

              <!-- 排序按钮 -->
               <button 
                 @click="toggleSort"
                 class="flex items-center gap-2 px-4 py-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex-shrink-0"
              >
                 <span class="text-xs font-bold text-slate-400 uppercase">排序</span>
                 <span class="text-sm font-bold text-slate-700 dark:text-slate-200 min-w-[4em] text-right">{{ getSortLabel(sortBy) }}</span>
                 <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
              </button>
          </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && filteredItems.length === 0" class="flex-1 flex flex-col items-center justify-center py-20 min-h-[400px]">
       <div class="w-24 h-24 rounded-[2.5rem] bg-slate-100 dark:bg-slate-800/80 flex items-center justify-center mb-6 shadow-inner">
         <svg class="w-12 h-12 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
           <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
         </svg>
       </div>
       <h3 class="text-xl font-black text-slate-700 dark:text-slate-300 tracking-tight">暂无媒体内容</h3>
       <p class="mt-2 text-slate-400 font-medium text-sm">
         {{ activeTab === 'all' ? '媒体库空空如也，快去添加订阅吧' : '当前筛选条件下没有找到内容' }}
       </p>
    </div>

    <!-- 媒体库网格 -->
    <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6 px-1 pb-20">
      <div 
        v-for="item in filteredItems" 
        :key="item.path"
        class="group relative flex flex-col cursor-pointer"
        @click="item.season_count <= 1 ? handlePlay(item) : null"
      >
         <!-- Image Container -->
         <div class="relative aspect-[2/3] rounded-2xl overflow-hidden shadow-lg bg-slate-200 dark:bg-slate-800 transition-all duration-500 ease-out group-hover:shadow-2xl group-hover:shadow-cyan-500/20 group-hover:-translate-y-2 z-10 w-full">
            
            <img 
              v-if="item.poster_url" 
              :src="item.poster_url" 
              class="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-110"
              loading="lazy"
              @error="handleImageError"
            />
            <div v-else class="w-full h-full flex items-center justify-center text-slate-400 bg-slate-100 dark:bg-slate-800">
               <span class="text-xs font-bold uppercase tracking-widest opacity-50">No Poster</span>
            </div>

            <!-- Gradient Overlay -->
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60 group-hover:opacity-80 transition-opacity"></div>
            
            <!-- Tags (Top Left) -->
            <div class="absolute top-3 left-3 flex flex-col gap-2 items-start opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
               <span v-if="item.is_subscribed" class="bg-cyan-500 text-white text-[10px] font-black px-2 py-1 rounded-lg shadow-lg shadow-cyan-500/30 backdrop-blur-md">
                  已订阅
               </span>
               <span v-if="item.status" :class="getStatusBadge(item.status).color" class="text-white text-[10px] font-black px-2 py-1 rounded-lg shadow-lg backdrop-blur-md bg-opacity-90">
                  {{ getStatusBadge(item.status).text }}
               </span>
               <span v-if="item.vote_average > 0" class="bg-yellow-400 text-black text-[10px] font-black px-2 py-1 rounded-lg shadow-lg shadow-yellow-400/30 backdrop-blur-md">
                  ★ {{ item.vote_average.toFixed(1) }}
               </span>
            </div>

            <!-- Delete Button (Top Right) -->
            <button 
               @click.stop="openDeleteModal(item)"
               class="absolute top-3 right-3 z-30 p-2 rounded-xl bg-black/40 hover:bg-red-500/80 backdrop-blur-md text-white/70 hover:text-white transition-all opacity-0 group-hover:opacity-100 hover:shadow-lg hover:shadow-red-500/30 translate-y-[-10px] group-hover:translate-y-0"
               title="删除"
            >
               <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            </button>

            <!-- Play Button Overlay -->
            <div class="absolute inset-0 flex items-center justify-center z-20 pointer-events-none">
               <button 
                  @click.stop="handlePlay(item)"
                  class="pointer-events-auto w-16 h-16 rounded-full flex items-center justify-center text-white shadow-2xl 
                         opacity-0 group-hover:opacity-100 
                         translate-y-4 group-hover:translate-y-0
                         scale-90 group-hover:scale-100
                         bg-white/0 group-hover:bg-white/20
                         backdrop-blur-none group-hover:backdrop-blur-md
                         border border-transparent group-hover:border-white/40
                         transition-all duration-500 ease-out
                         hover:bg-white/30 hover:scale-110"
               >
                 <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"></path></svg>
               </button>
            </div>

            <!-- Bottom Info -->
            <div class="absolute bottom-0 left-0 right-0 p-4 pt-8 flex items-end justify-between text-white">
                <span v-if="item.air_day !== null" class="text-[10px] font-bold px-1.5 py-0.5 bg-black/40 backdrop-blur-md rounded border border-white/10">
                   {{ getWeekdayStr(item.air_day) }}
                </span>
                <span class="text-[10px] font-bold opacity-80 font-mono tracking-wider">
                   {{ item.year || '' }}
                </span>
            </div>
         </div>

         <!-- Title & Meta -->
         <div class="mt-4 px-1 group-hover:translate-x-1 transition-transform duration-300">
            <h3 class="text-sm font-bold text-slate-800 dark:text-slate-100 line-clamp-1 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors" :title="item.title">
              {{ item.title }}
            </h3>
            <div class="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium">
               <span>{{ item.season_count }} 季</span>
               <span v-if="item.episode_count" class="w-1 h-1 rounded-full bg-slate-300 dark:bg-slate-600"></span>
               <!-- <span> TODO: EP count </span> -->
            </div>
         </div>
      </div>
    </div>

    <!-- Cinematic Video Player Overlay -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="showPlayer" class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6" role="dialog" aria-modal="true">
        
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/95 backdrop-blur-2xl transition-opacity" @click="closePlayer"></div>

        <!-- Content Container -->
        <div class="relative w-full max-w-7xl bg-black rounded-3xl overflow-hidden shadow-2xl ring-1 ring-white/10 flex flex-col md:flex-row h-[85vh] md:h-auto md:aspect-video animate-in zoom-in-95 duration-300">
           
           <!-- Close Button -->
           <button @click="closePlayer" class="absolute top-4 right-4 z-50 p-2 rounded-full bg-black/50 hover:bg-white/20 text-white/50 hover:text-white transition-all backdrop-blur-md group">
               <svg class="w-6 h-6 group-hover:rotate-90 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
           </button>

           <!-- Player Section -->
           <div class="flex-1 relative bg-black flex items-center justify-center group/player">
              <VideoPlayer 
                   v-if="currentVideo"
                   :option="{
                       url: currentVideo.stream_url,
                       poster: currentItem?.poster_url,
                       title: currentItem?.title + ' - ' + currentVideo.name,
                   }"
                   class="w-full h-full"
                />
           </div>

           <!-- Sidebar (Episode Selector) -->
           <div class="w-full md:w-80 bg-gray-900/50 backdrop-blur-xl border-l border-white/5 flex flex-col">
              <div class="p-6 border-b border-white/5 bg-gray-900/50">
                 <h3 class="text-xl font-bold text-white line-clamp-1">{{ currentItem?.title }}</h3>
                 <!-- Show Clean Name / TMDB Title -->
                 <p class="text-indigo-400 text-sm font-medium mt-1 truncate" :title="currentVideo?.name">
                    {{ currentVideo ? (currentVideo.display_name || currentVideo.name) : '选择剧集' }}
                 </p>
                 
                 <!-- Episode Summary -->
                 <div v-if="currentVideo?.summary" class="mt-4 animate-in fade-in slide-in-from-top-1 duration-500">
                    <p class="text-[11px] text-gray-400 line-clamp-6 leading-relaxed bg-white/5 p-3 rounded-xl border border-white/5 overflow-y-auto max-h-32">
                       {{ currentVideo.summary }}
                    </p>
                 </div>
              </div>

              <!-- Season Tabs -->
              <div v-if="sortedSeasons.length > 1" class="flex items-center gap-2 px-4 py-3 overflow-x-auto scrollbar-hide border-b border-white/5 bg-black/20">
                  <button 
                     v-for="s in sortedSeasons" 
                     :key="s"
                     @click="activeSeason = s"
                     :class="[
                       activeSeason === s ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' : 'bg-white/5 text-gray-400 hover:text-white',
                       'px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition-all'
                     ]"
                  >
                     {{ s }}
                  </button>
              </div>
              
              <div class="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-thin scrollbar-thumb-gray-700">
                 <button 
                    v-for="vid in (groupedEpisodes[activeSeason] || [])" 
                    :key="vid.name"
                    @click="selectEpisode(vid)"
                    :class="[
                      currentVideo?.name === vid.name 
                        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20' 
                        : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white',
                      'w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 flex items-center justify-between group'
                    ]"
                 >
                    <span class="truncate pr-2" :title="vid.name">{{ vid.display_name || vid.name }}</span>
                    <span v-if="currentVideo?.name === vid.name" class="flex h-2 w-2 shrink-0 relative">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                    </span>
                 </button>
              </div>
           </div>

        </div>
      </div>
    </Transition>

    <!-- Delete Confirmation Modal -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div v-if="showDeleteModal" class="fixed inset-0 z-[60] flex items-center justify-center p-4" role="dialog" aria-modal="true">
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm" @click="showDeleteModal = false"></div>
        
        <!-- Modal Card -->
        <div class="relative w-full max-w-md bg-white dark:bg-slate-900 rounded-3xl p-6 shadow-2xl ring-1 ring-black/5 dark:ring-white/10">
          <h3 class="text-xl font-black text-slate-800 dark:text-white mb-2">删除确认</h3>
          <p class="text-slate-500 dark:text-slate-400 text-sm mb-6">
            确定要从媒体库中移除 <span class="font-bold text-slate-700 dark:text-slate-200">"{{ itemToDelete?.title }}"</span> 吗？
          </p>
          
          <div class="space-y-3 mb-8">
             <label class="flex items-center gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                <input type="checkbox" v-model="deleteOptions.deleteFile" class="w-5 h-5 rounded border-slate-300 text-red-500 focus:ring-red-500/30">
                <div class="flex flex-col">
                   <span class="text-sm font-bold text-slate-700 dark:text-slate-200">同时删除本地文件</span>
                   <span class="text-xs text-slate-400">将永久删除磁盘上的媒体文件</span>
                </div>
             </label>
             
             <label v-if="itemToDelete?.is_subscribed" class="flex items-center gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                <input type="checkbox" v-model="deleteOptions.cancelSubscription" class="w-5 h-5 rounded border-slate-300 text-cyan-500 focus:ring-cyan-500/30">
                <div class="flex flex-col">
                   <span class="text-sm font-bold text-slate-700 dark:text-slate-200">同时取消订阅</span>
                   <span class="text-xs text-slate-400">将停止接收该系列的后续更新</span>
                </div>
             </label>
          </div>
          
          <div class="flex items-center gap-3">
             <button @click="showDeleteModal = false" class="flex-1 py-3 rounded-xl font-bold text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors">
               取消
             </button>
             <button 
               @click="confirmDelete" 
               :disabled="deleteLoading"
               class="flex-1 py-3 rounded-xl font-bold text-white bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/30 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
             >
               <svg v-if="deleteLoading" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
               {{ deleteLoading ? '删除中...' : '确认删除' }}
             </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { scanLibrary, getLibraryItems, getLibraryItemEpisodes, deleteLibraryItem } from '@/api/library'
import { useMessage } from '@/composables/useMessage'
import VideoPlayer from '@/components/VideoPlayer.vue'

const message = useMessage()
const items = ref([])
const loading = ref(false)

// Player State
const showPlayer = ref(false)
const currentItem = ref(null)
const episodes = ref([])
const currentVideo = ref(null)
const playerLoading = ref(false)

// Filter State
const filterStatus = ref('all')
const filterDay = ref('all')
const onlySubscribed = ref(false)
const sortBy = ref('updated')
const activeTab = ref('all')

const setMainFilter = (id) => {
  activeTab.value = id
  
  // Reset base filters
  filterStatus.value = 'all'
  onlySubscribed.value = false
  
  if (id === 'current') filterStatus.value = 'current'
  if (id === 'ended') filterStatus.value = 'ended'
  if (id === 'subscribed') onlySubscribed.value = true
}

const sortLabels = {
  updated: '更新时间',
  rating: '最高评分',
  year: '发行年份',
  title: '名称排序'
}

const getSortLabel = (key) => sortLabels[key] || key

const toggleSort = () => {
  const opts = ['updated', 'rating', 'year', 'title']
  const idx = opts.indexOf(sortBy.value)
  sortBy.value = opts[(idx + 1) % opts.length]
}

// Logic for Season Grouping
const activeSeason = ref('')

const groupedEpisodes = computed(() => {
  const groups = {}
  if (!episodes.value) return {}
  
  episodes.value.forEach(ep => {
     let seasonName = '其他'
     
     // Use backend provided season number if available
     if (ep.season !== null && ep.season !== undefined) {
         // Filter out Season 0 (Specials/OVAs) based on user's "Regular Only" request
         if (ep.season === 0) return
         seasonName = `第 ${ep.season} 季`
     } else {
         // Fallback to parsing if backend didn't provide it
         const folderMatch = ep.path.match(/Season\s*(\d+)/i) || ep.path.match(/S(\d+)/)
         if (folderMatch) {
            const sNum = parseInt(folderMatch[1])
            if (sNum === 0) return // Skip Specials
            seasonName = `第 ${sNum} 季`
         } else {
            const fileMatch = ep.name.match(/S(\d+)E/i)
            if (fileMatch) {
                 const sNum = parseInt(fileMatch[1])
                 if (sNum === 0) return // Skip Specials
                 seasonName = `第 ${sNum} 季`
            }
         }
     }
     if (!groups[seasonName]) groups[seasonName] = []
     groups[seasonName].push(ep)
  })
  return groups
})

const sortedSeasons = computed(() => {
  return Object.keys(groupedEpisodes.value).sort((a,b) => {
     if (a === '其他') return 1
     if (b === '其他') return -1
     const numA = parseInt(a.match(/\d+/) || 0)
     const numB = parseInt(b.match(/\d+/) || 0)
     return numA - numB
  })
})

// Auto select season when episodes load
watch(episodes, (newVal) => {
    if (newVal.length > 0 && sortedSeasons.value.length > 0) {
        // If current video exists, find its season
        if (currentVideo.value) {
            // Find which season contains this video
            const found = sortedSeasons.value.find(s => groupedEpisodes.value[s].find(e => e.name === currentVideo.value.name))
            if (found) {
                activeSeason.value = found
                return
            }
        }
        activeSeason.value = sortedSeasons.value[0]
    }
})

// Validation helper for clean names
const getEpisodeName = (name) => {
    // Basic cleanup: remove extension
    let clean = name.replace(/\.(mp4|mkv|avi|webm)$/i, '')
    // remove bracket tags optionally? nice t have
    // clean = clean.replace(/\[.*?\]/g, '').trim() 
    return clean
}



const filteredItems = computed(() => {
  let res = [...items.value]
  
  // Filter by Subscription
  if (onlySubscribed.value) {
    res = res.filter(i => i.is_subscribed)
  }
  
  // Filter by Status
  if (filterStatus.value !== 'all') {
    if (filterStatus.value === 'current') {
      res = res.filter(i => i.status === 'Returning Series' || i.status === 'In Production')
    } else if (filterStatus.value === 'ended') {
      res = res.filter(i => i.status === 'Ended' || i.status === 'Canceled')
    }
  }
  
  // Filter by Day
  if (filterDay.value !== 'all') {
    res = res.filter(i => i.air_day === parseInt(filterDay.value))
  }
  
  // Sort
  res.sort((a, b) => {
    switch(sortBy.value) {
      case 'rating':
        return (b.vote_average || 0) - (a.vote_average || 0)
      case 'year':
        return (parseInt(b.year) || 0) - (parseInt(a.year) || 0)
      case 'title':
        return a.title.localeCompare(b.title, 'zh')
      case 'updated':
      default:
        // Default to updated_at desc
        return (new Date(b.updated_at) || 0) - (new Date(a.updated_at) || 0)
    }
  })
  
  return res
})

const loadItems = async () => {
  try {
    loading.value = true
    items.value = await getLibraryItems()
  } catch (error) {
    message.error('加载媒体库失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const startScan = async () => {
  try {
    message.info('正在启动后台扫描...')
    const res = await scanLibrary()
    if (res.status === 'success') {
      message.success('扫描任务已启动，请稍后刷新查看')
    }
  } catch (error) {
    message.error('启动扫描失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handlePlay = async (item) => {
  try {
    playerLoading.value = true
    // Fetch episodes
    const eps = await getLibraryItemEpisodes(item.id)
    if (eps.length === 0) {
      message.warning('未找到该系列的可播放视频')
      return
    }
    
    currentItem.value = item
    episodes.value = eps
    showPlayer.value = true
    
    // Auto play first episode
    currentVideo.value = eps[0]
  } catch (error) {
    message.error('获取视频列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    playerLoading.value = false
  }
}

const closePlayer = () => {
  showPlayer.value = false
  currentVideo.value = null
  episodes.value = []
}

const selectEpisode = (video) => {
  currentVideo.value = video
}

const handleImageError = (e) => {
  e.target.style.display = 'none'
  e.target.parentElement.classList.add('bg-gray-100', 'dark:bg-gray-800', 'flex', 'items-center', 'justify-center')
  e.target.parentElement.innerHTML = `
    <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  `
}

const getWeekdayStr = (day) => {
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return days[day] || ''
}

const getStatusBadge = (status) => {
  if (status === 'Ended' || status === 'Canceled') return { text: '已完结', color: 'bg-slate-500' }
  if (status === 'Returning Series' || status === 'In Production') return { text: '连载中', color: 'bg-emerald-500' }
  return { text: status, color: 'bg-blue-500' }
}

onMounted(() => {
  loadItems()
})

// Delete Logic
const showDeleteModal = ref(false)
const itemToDelete = ref(null)
const deleteLoading = ref(false)
const deleteOptions = ref({
  deleteFile: false,
  cancelSubscription: true
})

const openDeleteModal = (item) => {
  itemToDelete.value = item
  // Default options:
  // - deleteFile: false (safer)
  // - cancelSubscription: true (if subscribed)
  deleteOptions.value = {
    deleteFile: false,
    cancelSubscription: !!item.is_subscribed
  }
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!itemToDelete.value) return
  
  try {
    deleteLoading.value = true
    await deleteLibraryItem(itemToDelete.value.id, { 
      delete_file: deleteOptions.value.deleteFile,
      cancel_subscription: deleteOptions.value.cancelSubscription
    })
    
    message.success('删除成功')
    showDeleteModal.value = false
    
    // Remove from local list instantly
    items.value = items.value.filter(i => i.id !== itemToDelete.value.id)
    itemToDelete.value = null
  } catch (error) {
    message.error('删除失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    deleteLoading.value = false
  }
}
</script>
