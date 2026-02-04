<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { 
    searchMikan, 
    listSubscriptions, 
    createSubscription, 
    updateSubscription, 
    deleteSubscription, 
    pauseSubscription, 
    resumeSubscription, 
    checkSubscription,
    getSubscriptionItems
} from "@/api/subscriptions";
import BaseConfirmDialog from "@/components/core/BaseConfirmDialog.vue";
import { Switch, Dialog, TransitionRoot, TransitionChild, DialogPanel, DialogTitle } from '@headlessui/vue';
import { getSettingsByCategory } from "@/api/settings";
import { getTextInitial } from "@/api/utils";

// State
const activeTab = ref("my_subscriptions"); // my_subscriptions, search
const subscriptions = ref([]);
const searchKeyword = ref("");
const searchResults = ref([]);
const loading = ref(false);
const searching = ref(false);
const message = ref({ type: "", text: "" });

// Edit/Create Dialog State
const showDialog = ref(false);
const editingSubscription = ref(null); // If null, creating new
const dialogForm = ref({
    mikan_id: "",
    title: "",
    cover_url: "",
    subgroup_id: "",
    subgroup_name: "",
    filter_keywords: [],
    exclude_keywords: [],
    save_path: "",
    category: "hoshino",
    auto_download: true,
    extra_vars: {
        series_name: "",
        season: 1,
        episode_offset: 0
    }
});
const mikanDetail = ref(null); // Store detail for subgroup selection
const loadingDetail = ref(false);
const targetLibraryPath = ref("/downloads/anime"); // Default, will fetch from settings

onMounted(async () => {
    // Determine if we need to call loadSubscriptions()
    // Usually it's called on mount. I'll call it here to be safe and ensure init.
    // If it's already called elsewhere, a double call is cheap (just a list fetch).
    loadSubscriptions(); 

    try {
        const appSettings = await getSettingsByCategory("app"); // Returns list or dict? 
        // Backend returns list of objects for "app" category
        const targetSetting = appSettings.find(s => s.key === "app.target_library_path");
        if (targetSetting && targetSetting.value) {
            targetLibraryPath.value = targetSetting.value;
        }
    } catch (e) {
        console.error("Failed to fetch target_library_path", e);
    }
});

// Confirm Dialog
const showConfirm = ref(false);
const confirmMsg = ref("");
const confirmAction = ref(null);

// RSS Items Dialog
const showItemsDialog = ref(false);
const currentRSSItems = ref([]);
const currentSubTitle = ref("");

// --- Methods ---

const loadSubscriptions = async () => {
    loading.value = true;
    try {
        subscriptions.value = await listSubscriptions();
    } catch (e) {
        showMessage("error", "加载订阅失败: " + e.message);
    } finally {
        loading.value = false;
    }
};

const handleSearch = async () => {
    if (!searchKeyword.value.trim()) return;
    searching.value = true;
    searchResults.value = [];
    try {
        searchResults.value = await searchMikan(searchKeyword.value);
        if (searchResults.value.length === 0) {
            showMessage("info", "未找到相关番剧");
        }
    } catch (e) {
        showMessage("error", "搜索失败: " + e.message);
    } finally {
        searching.value = false;
    }
};

const openSubscribeDialog = async (anime) => {
    // anime: { mikan_id, title, cover_url }
    editingSubscription.value = null; // Create mode
    dialogForm.value = {
        mikan_id: anime.mikan_id,
        title: anime.title,
        cover_url: anime.cover_url,
        subgroup_id: "",
        subgroup_name: "",
        filter_keywords: [],
        exclude_keywords: [],
        save_path: "/downloads/anime/" + anime.title, // Default suggestion
        category: "hoshino",
        auto_download: true,
        extra_vars: {
            series_name: anime.title,
            season: 1,
            episode_offset: 0
        },
        filter_regex: ""
    };
    
    showDialog.value = true;
    await fetchMikanDetail(anime.mikan_id);
};

const openEditDialog = async (sub) => {
    editingSubscription.value = sub;
    dialogForm.value = {
        mikan_id: sub.mikan_id,
        title: sub.title,
        cover_url: sub.cover_url,
        subgroup_id: sub.subgroup_id,
        subgroup_name: sub.subgroup_name,
        filter_keywords: [...sub.filter_keywords], // Copy array
        exclude_keywords: [...sub.exclude_keywords],
        save_path: sub.save_path,
        category: sub.category,
        auto_download: sub.auto_download,
        extra_vars: { ...sub.extra_vars },
        filter_regex: sub.filter_regex || ""
    };
    showDialog.value = true;
    await fetchMikanDetail(sub.mikan_id);
};

// Use import dynamically or create api? 
// We need getBangumiDetail from api which actually calls mikan service
import { getBangumiDetail } from "@/api/subscriptions";

const currentPreviewVideos = computed(() => {
    if (!dialogForm.value.subgroup_id || !mikanDetail.value) return [];
    const sg = mikanDetail.value.subgroups.find(s => s.id === dialogForm.value.subgroup_id);
    return sg ? (sg.videos || []) : [];
});

const filteredPreviewVideos = computed(() => {
    const videos = currentPreviewVideos.value;
    const regexStr = dialogForm.value.filter_regex;
    if (!regexStr) return videos;
    
    try {
        const regex = new RegExp(regexStr, 'i'); // Case insensitive
        return videos.filter(v => regex.test(v.title));
    } catch (e) {
        return videos; // Invalid regex, show all (or could handle error visual)
    }
});

let pathUpdateTimer = null;

// Auto-update save path for new subscriptions (Standard: Base/Initial/Title/Season {n})
watch(() => [dialogForm.value.title, dialogForm.value.extra_vars.season, targetLibraryPath.value], ([newTitle, newSeason, newPath]) => {
    if (!editingSubscription.value && newTitle) {
        if (pathUpdateTimer) clearTimeout(pathUpdateTimer);
        
        pathUpdateTimer = setTimeout(async () => {
            const seasonNum = newSeason || 1;
            const safeTitle = newTitle.replace(/[\\/:*?"<>|]/g, "_");
            
            let initial = "#";
            try {
                const res = await getTextInitial(newTitle);
                if (res && res.initial) initial = res.initial;
            } catch (e) {
                console.error("Failed to get initial", e);
            }

            // Use the newPath (which is targetLibraryPath)
            const basePath = (newPath || "/downloads/anime").replace(/\/$/, "");
            dialogForm.value.save_path = `${basePath}/${initial}/${safeTitle}/Season ${seasonNum}`;
        }, 300);
    }
});

const fetchMikanDetail = async (mikanId) => {
    loadingDetail.value = true;
    mikanDetail.value = null;
    try {
        const detail = await getBangumiDetail(mikanId);
        mikanDetail.value = detail;
        
        // Auto-fill enriched data if creating (editing might have custom overrides)
        if (!editingSubscription.value) {
            if (detail.suggested_title) {
                dialogForm.value.title = detail.suggested_title;
                dialogForm.value.extra_vars.series_name = detail.suggested_title;
                // Update save_path automatically
                dialogForm.value.save_path = "/downloads/anime/" + detail.suggested_title;
            }
            if (detail.suggested_season) {
                dialogForm.value.extra_vars.season = detail.suggested_season;
            }
        }
        
        // If editing and no subgroup selected, or new, try to select first or match?
        // Usually user selects manually.
    } catch (e) {
        showMessage("error", "获取字幕组信息失败");
    } finally {
        loadingDetail.value = false;
    }
};

const saveSubscription = async () => {
    try {
        // Validate
        if (!dialogForm.value.save_path) {
            showMessage("error", "请填写保存路径");
            return;
        }
        
        // Populate subgroup name if id selected
        if (dialogForm.value.subgroup_id && mikanDetail.value) {
            const sg = mikanDetail.value.subgroups.find(s => s.id === dialogForm.value.subgroup_id);
            if (sg) dialogForm.value.subgroup_name = sg.name;
        }

        if (editingSubscription.value) {
            await updateSubscription(editingSubscription.value.id, dialogForm.value);
            showMessage("success", "订阅已更新");
        } else {
            await createSubscription(dialogForm.value);
            showMessage("success", "订阅创建成功");
            activeTab.value = "my_subscriptions"; // Switch tab
        }
        showDialog.value = false;
        loadSubscriptions();
    } catch (e) {
        showMessage("error", "保存失败: " + e.message);
    }
};

const deleteLocalFiles = ref(false);

const handleDelete = (sub) => {
    deleteLocalFiles.value = false;
    confirmMsg.value = `确定要取消订阅 "${sub.title}" 吗？`;
    confirmAction.value = async () => {
        try {
            await deleteSubscription(sub.id, deleteLocalFiles.value);
            showMessage("success", "订阅已删除");
            loadSubscriptions();
        } catch (e) {
            showMessage("error", "删除失败: " + e.message);
        }
    };
    // Store current sub for display in dialog if needed, or just use closure
    currentSubTitle.value = sub.title; // reusing currentSubTitle or confirmMsg
    // Wait, confirmMsg is string. I want to show path.
    // I need to pass the path to the dialog or store it.
    // Let's store currentDeletingSub
    editingSubscription.value = sub; // abusing editingSubscription? No safer to add new ref.
    
    showConfirm.value = true;
};

const togglePause = async (sub) => {
    try {
        if (sub.status === 'active') {
            await pauseSubscription(sub.id);
            sub.status = 'paused';
        } else {
            await resumeSubscription(sub.id);
            sub.status = 'active';
        }
    } catch(e) { showMessage("error", "操作失败"); }
};

const handleCheck = async (sub) => {
    showMessage("info", "正如请求检查更新...");
    try {
        await checkSubscription(sub.id);
        showMessage("success", "检查完成");
        loadSubscriptions(); // Refresh last_check_at
    } catch(e) {
        showMessage("error", "检查失败");
    }
};

const viewItems = async (sub) => {
    currentSubTitle.value = sub.title;
    try {
        currentRSSItems.value = await getSubscriptionItems(sub.id);
        showItemsDialog.value = true;
    } catch(e) { showMessage("error", "获取记录失败"); }
};

const showMessage = (type, text) => {
    message.value = { type, text };
    setTimeout(() => message.value = { type: "", text: "" }, 3000);
};

// Keywords input helper
const newKeyword = ref("");
const addKeyword = (isExclude=false) => {
    const val = newKeyword.value.trim();
    if (!val) return;
    if (isExclude) {
        if (!dialogForm.value.exclude_keywords.includes(val)) dialogForm.value.exclude_keywords.push(val);
    } else {
        if (!dialogForm.value.filter_keywords.includes(val)) dialogForm.value.filter_keywords.push(val);
    }
    newKeyword.value = "";
};
const removeKeyword = (idx, isExclude=false) => {
    if (isExclude) dialogForm.value.exclude_keywords.splice(idx, 1);
    else dialogForm.value.filter_keywords.splice(idx, 1);
};

const onSubgroupChange = () => {
    // Reset filters when switching subgroups to avoid "no result" state
    selectedTags.value = [];
    dialogForm.value.filter_regex = "";
    // Maybe keep keywords?
};

// --- Smart Filter Logic ---
const advancedMode = ref(false);
const selectedTags = ref([]);

// Extract common tags from current video list
const commonTags = computed(() => {
    const videos = currentPreviewVideos.value;
    if (!videos.length) return [];
    
    const tagCounts = {};
    const regex = /\[([^\]]+)\]/g; // Extract content inside []
    
    videos.forEach(v => {
        let match;
        // Reset regex index
        regex.lastIndex = 0; 
        while ((match = regex.exec(v.title)) !== null) {
            const tag = match[1].trim();
            // Filter out purely numeric tags like episode numbers if possible, 
            // but usually e.g. [01] is useful for some, though we want metadata tags.
            // Let's filter out very short numeric ones maybe?
            if (/^\d{1,3}$/.test(tag) || tag.includes('x')) {
                 // skip likely episode numbers or resolutions like 1920x1080 if inside brackets?
                 // Actually [1080p] is fine. [01] is episode.
                 // Let's keep all for now, user can choose.
            }
            tagCounts[tag] = (tagCounts[tag] || 0) + 1;
        }
    });

    // Also look for common keywords if not in brackets?
    // "MP4", "MKV", "GB", "BIG5", "CHS"
    const keywords = ["MP4", "MKV", "CHS", "BIG5", "CHT", "简日", "繁日"];
    videos.forEach(v => {
        keywords.forEach(kw => {
            if (v.title.toUpperCase().includes(kw) && !Object.keys(tagCounts).some(t => t.toUpperCase().includes(kw))) {
                 // Only add if not already captured by brackets
                 // Actually simply checking presence is good
                 tagCounts[kw] = (tagCounts[kw] || 0) + 1;
            }
        });
    });

    // Sort by frequency
    return Object.entries(tagCounts)
        .sort((a, b) => b[1] - a[1]) // Descending freq
        .slice(0, 15) // Top 15 tags
        .map(e => e[0]);
});

const toggleTag = (tag) => {
    const idx = selectedTags.value.indexOf(tag);
    if (idx > -1) selectedTags.value.splice(idx, 1);
    else selectedTags.value.push(tag);
    updateRegexFromTags();
};

const updateRegexFromTags = () => {
    if (selectedTags.value.length === 0) {
        dialogForm.value.filter_regex = "";
        return;
    }
    // Construct regex that requires ALL tags to be present (lookaheads)
    // (?=.*Tag1)(?=.*Tag2)
    const pattern = selectedTags.value.map(t => `(?=.*${escapeRegExp(t)})`).join("");
    dialogForm.value.filter_regex = pattern;
};

const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Watch dialog open to reset state
watch(showDialog, (val) => {
    if (val) {
        selectedTags.value = [];
        advancedMode.value = !!dialogForm.value.filter_regex; // Auto advanced if existing regex is complex?
        // Actually if existing regex doesn't match our tag pattern, switch to advanced.
        // For now simple default.
    }
});
</script>

<template>
<div class="h-full flex flex-col gap-6">
    <!-- 页面标题和标签页 -->
    <div class="flex-shrink-0">
      <div class="flex items-end justify-between mb-4">
        <div class="flex items-center gap-3">
          <span class="w-2 h-10 bg-cyan-500 rounded-full shadow-lg shadow-cyan-500/30"></span>
          <div>
            <h1 class="text-4xl font-black text-slate-800 dark:text-white tracking-tight">订阅管理</h1>
            <p class="text-xs font-bold text-slate-400 mt-1 uppercase tracking-widest">Subscription Manager</p>
          </div>
        </div>
        
        <!-- 标签页切换 -->
        <div class="bg-white/70 dark:bg-slate-800/70 backdrop-blur-xl p-1.5 rounded-2xl flex gap-2 shadow-xl border border-white/60 dark:border-white/10">
            <button 
                @click="activeTab = 'my_subscriptions'"
                class="relative px-6 py-3 rounded-xl text-sm font-bold transition-all duration-300"
                :class="activeTab === 'my_subscriptions' ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'"
            >
                <span class="relative z-10">我的订阅</span>
                <div v-if="activeTab === 'my_subscriptions'" class="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-transparent rounded-xl"></div>
            </button>
            <button 
                @click="activeTab = 'search'"
                class="relative px-6 py-3 rounded-xl text-sm font-bold transition-all duration-300"
                :class="activeTab === 'search' ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'"
            >
                <span class="relative z-10">搜索番剧</span>
                <div v-if="activeTab === 'search'" class="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-transparent rounded-xl"></div>
            </button>
        </div>
      </div>
    </div>

    <!-- Message Alert -->
    <Transition
        enter-active-class="transition duration-100 ease-out"
        enter-from-class="transform scale-95 opacity-0"
        enter-to-class="transform scale-100 opacity-100"
        leave-active-class="transition duration-75 ease-in"
        leave-from-class="transform scale-100 opacity-100"
        leave-to-class="transform scale-95 opacity-0"
    >
        <div v-if="message.text" :class="[
            'fixed top-24 right-6 z-50 px-6 py-3 rounded-2xl text-sm font-bold shadow-2xl backdrop-blur-md flex items-center gap-3',
            message.type === 'error' ? 'bg-red-500/90 text-white shadow-red-500/20' : 
            message.type === 'success' ? 'bg-emerald-500/90 text-white shadow-emerald-500/20' :
            'bg-blue-500/90 text-white shadow-blue-500/20'
        ]">
            <svg v-if="message.type==='success'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" /></svg>
            <svg v-else-if="message.type==='error'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
            <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            
            {{ message.text }}
        </div>
    </Transition>

    <!-- Content: My Subscriptions -->
    <div v-if="activeTab === 'my_subscriptions'" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-6">
        <div v-if="loading" class="col-span-full py-12 flex justify-center">
             <div class="animate-spin rounded-full h-10 w-10 border-4 border-cyan-500/30 border-t-cyan-500"></div>
        </div>
        
        <div v-else-if="subscriptions.length === 0" class="col-span-full py-20 text-center">
            <div class="inline-flex justify-center items-center w-24 h-24 bg-slate-50 dark:bg-white/5 rounded-[2rem] mb-6">
                <svg class="w-10 h-10 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
            </div>
            <p class="text-slate-400 font-bold text-lg">暂无订阅</p>
            <p class="text-slate-400/50 text-sm mt-1">去搜搜看有没有想追的新番吧</p>
        </div>

        <div 
            v-for="sub in subscriptions" 
            :key="sub.id"
            class="group relative aspect-[2/3] bg-slate-900 rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl hover:shadow-cyan-500/20 transition-all duration-300 hover:-translate-y-1"
        >
            <!-- Background Image -->
            <img v-if="sub.cover_url" :src="sub.cover_url" class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" />
            <div v-else class="absolute inset-0 bg-slate-800 flex items-center justify-center">
                <span class="text-slate-600 font-bold text-xs uppercase tracking-widest">No Cover</span>
            </div>
            
            <!-- Gradient Overlay -->
            <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-80 group-hover:opacity-90 transition-opacity"></div>
            
            <!-- Content -->
            <div class="absolute inset-0 p-4 flex flex-col justify-end">
                <div class="transform translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
                    <div class="flex items-start gap-2 mb-1">
                        <span v-if="sub.extra_vars?.season" class="shrink-0 mt-0.5 bg-yellow-400 text-black text-[10px] font-black px-1.5 py-0.5 rounded shadow-lg shadow-yellow-400/20">
                            S{{ sub.extra_vars.season }}
                        </span>
                        <h3 class="text-white font-bold text-base leading-tight line-clamp-2 drop-shadow-md">{{ sub.title }}</h3>
                    </div>
                    
                    <div class="flex items-center gap-2 text-[10px] text-white/70 font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-75">
                         <span v-if="sub.subgroup_name" class="truncate max-w-[80px]">{{ sub.subgroup_name }}</span>
                         <span v-else>全部分组</span>
                         <span v-if="sub.bangumi_rating" class="text-amber-400">★ {{ sub.bangumi_rating }}</span>
                    </div>
                </div>
            </div>

            <!-- Status Dot -->
            <div class="absolute top-3 right-3">
                 <div class="flex h-3 w-3 relative">
                    <span v-if="sub.status === 'active'" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-3 w-3" :class="sub.status === 'active' ? 'bg-emerald-500' : 'bg-slate-500'"></span>
                 </div>
            </div>

            <!-- Hover Actions Overlay -->
            <div class="absolute inset-0 bg-black/60 backdrop-blur-[2px] opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col items-center justify-center gap-3 p-4 z-10" v-if="!loading">
                <div class="grid grid-cols-2 gap-3 w-full max-w-[160px]">
                    <button @click.stop="togglePause(sub)" class="flex flex-col items-center justify-center gap-1 p-2 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors backdrop-blur-md">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                           <path v-if="sub.status==='active'" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                           <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span class="text-[10px] font-bold">{{ sub.status==='active' ? '暂停' : '恢复' }}</span>
                    </button>
                    <button @click.stop="handleCheck(sub)" class="flex flex-col items-center justify-center gap-1 p-2 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/40 text-cyan-400 hover:text-cyan-200 transition-colors backdrop-blur-md">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                         <span class="text-[10px] font-bold">检查</span>
                    </button>
                    <button @click.stop="openEditDialog(sub)" class="flex flex-col items-center justify-center gap-1 p-2 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors backdrop-blur-md">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                         <span class="text-[10px] font-bold">编辑</span>
                    </button>
                    <button @click.stop="handleDelete(sub)" class="flex flex-col items-center justify-center gap-1 p-2 rounded-xl bg-red-500/20 hover:bg-red-500/40 text-red-400 hover:text-red-200 transition-colors backdrop-blur-md">
                        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                         <span class="text-[10px] font-bold">删除</span>
                    </button>
                </div>
                
                <button @click.stop="viewItems(sub)" class="mt-2 text-[10px] text-white/50 hover:text-white transition-colors flex items-center gap-1">
                    查看下载记录
                    <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" /></svg>
                </button>
            </div>
        </div>
    </div>

    <!-- 搜索内容 -->
    <div v-else-if="activeTab === 'search'" class="flex-1 flex flex-col gap-6">
        <div class="bg-white/70 dark:bg-slate-900/70 backdrop-blur-xl rounded-[2rem] p-8 border border-white/60 dark:border-white/10 shadow-xl">
          <div class="flex items-center gap-3 mb-6">
            <div class="p-2.5 rounded-2xl bg-cyan-500 text-white shadow-lg shadow-cyan-500/30">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div>
              <h2 class="text-lg font-black text-slate-900 dark:text-white tracking-tight">搜索番剧</h2>
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Search Anime</p>
            </div>
          </div>

          <div class="relative max-w-3xl mx-auto">
            <input 
                v-model="searchKeyword" 
                @keyup.enter="handleSearch"
                type="text" 
                placeholder="输入番剧名称搜索 Mikan..." 
                class="w-full h-16 pl-6 pr-20 rounded-2xl bg-slate-50/50 dark:bg-black/20 border border-slate-200/50 dark:border-white/10 shadow-lg focus:ring-4 focus:ring-cyan-500/20 outline-none text-slate-700 dark:text-white font-bold transition-all placeholder:text-slate-400"
            >
            <button 
                @click="handleSearch"
                class="absolute right-3 top-3 h-10 w-10 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-cyan-500/30 hover:scale-105 hover:shadow-xl hover:shadow-cyan-500/40 transition-all active:scale-95"
                :disabled="searching"
            >
                <svg v-if="!searching" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <div v-else class="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white"></div>
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
            <div 
                v-for="anime in searchResults" 
                :key="anime.mikan_id"
                class="group relative bg-white dark:bg-[#0f172a] rounded-2xl overflow-hidden cursor-pointer hover:shadow-2xl hover:shadow-cyan-500/20 transition-all duration-300"
                @click="openSubscribeDialog(anime)"
            >
                <div class="aspect-[3/4] overflow-hidden">
                    <img :src="anime.cover_url" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500">
                    <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                        <div class="bg-white text-slate-900 px-4 py-2 rounded-xl font-bold transform translate-y-4 group-hover:translate-y-0 transition-all shadow-xl">
                            订阅
                        </div>
                    </div>
                </div>
                <div class="p-3">
                    <h3 class="font-bold text-sm text-slate-700 dark:text-gray-200 line-clamp-2" :title="anime.title">{{ anime.title }}</h3>
                </div>
            </div>
        </div>
    </div>

    <!-- Edit/Create Dialog -->
    <TransitionRoot appear :show="showDialog" as="template">
        <Dialog as="div" @close="showDialog = false" class="relative z-50">
            <TransitionChild
                enter="duration-300 ease-out"
                enter-from="opacity-0"
                enter-to="opacity-100"
                leave="duration-200 ease-in"
                leave-from="opacity-100"
                leave-to="opacity-0"
            >
                <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" />
            </TransitionChild>

            <div class="fixed inset-0 overflow-y-auto">
                <div class="flex min-h-full items-center justify-center p-4">
                    <TransitionChild
                        enter="duration-300 ease-out"
                        enter-from="opacity-0 scale-95"
                        enter-to="opacity-100 scale-100"
                        leave="duration-200 ease-in"
                        leave-from="opacity-100 scale-100"
                        leave-to="opacity-0 scale-95"
                    >
                        <DialogPanel class="w-full max-w-5xl transform overflow-hidden rounded-3xl bg-white dark:bg-[#0f172a] border border-slate-100 dark:border-white/10 p-0 shadow-2xl transition-all flex flex-col max-h-[90vh] relative">
                            
                            <!-- Global Loading Overlay -->
                            <div v-if="loadingDetail" class="absolute inset-0 z-50 bg-white/80 dark:bg-[#0f172a]/80 backdrop-blur-sm flex flex-col items-center justify-center">
                                <div class="animate-spin rounded-full h-12 w-12 border-4 border-slate-200 dark:border-white/10 border-t-cyan-500 mb-4"></div>
                                <p class="text-sm font-bold text-slate-500 dark:text-slate-400">正在分析番剧信息...</p>
                            </div>

                            <!-- Header -->
                            <div class="px-8 py-6 border-b border-slate-100 dark:border-white/5 flex justify-between items-center bg-slate-50/50 dark:bg-white/5">
                                <DialogTitle as="h3" class="text-2xl font-black text-slate-800 dark:text-white">
                                    {{ editingSubscription ? '编辑订阅' : '新建订阅' }}
                                </DialogTitle>
                                <button @click="showDialog = false" class="p-2 rounded-full hover:bg-slate-200 dark:hover:bg-white/10 transition">
                                    <svg class="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
                                </button>
                            </div>

                            <div class="flex-1 overflow-y-auto p-8">
                                <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                                    
                                    <!-- Left: Basic Config (4 cols) -->
                                    <div class="lg:col-span-4 space-y-6">
                                        
                                        <!-- Cover & Title -->
                                        <div class="flex gap-4">
                                            <div class="w-24 h-32 rounded-xl bg-slate-100 dark:bg-slate-800 overflow-hidden shadow-md shrink-0">
                                                <img v-if="dialogForm.cover_url" :src="dialogForm.cover_url" class="w-full h-full object-cover">
                                            </div>
                                            <div class="flex-1 min-w-0 space-y-2">
                                                <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">番剧标题</label>
                                                <input v-model="dialogForm.title" class="w-full p-2 rounded-lg bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/5 text-sm font-bold text-slate-700 dark:text-white focus:ring-2 focus:ring-cyan-500">
                                                
                                                <div class="grid grid-cols-2 gap-2">
                                                    <div>
                                                        <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">季 (Season)</label>
                                                        <input type="number" v-model="dialogForm.extra_vars.season" class="w-full mt-1 p-2 rounded-lg bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/5 text-sm font-bold text-center text-slate-700 dark:text-white">
                                                    </div>
                                                    <div>
                                                        <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">偏移 (Offset)</label>
                                                        <input type="number" v-model="dialogForm.extra_vars.episode_offset" class="w-full mt-1 p-2 rounded-lg bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/5 text-sm font-bold text-center text-slate-700 dark:text-white">
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Subgroup Selection -->
                                        <div class="space-y-2">
                                            <label class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase">选择字幕组</label>
                                            <div class="relative">
                                                <select 
                                                    v-model="dialogForm.subgroup_id" 
                                                    @change="onSubgroupChange"
                                                    class="w-full p-3 pl-4 pr-10 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/5 font-bold text-slate-700 dark:text-white focus:ring-2 focus:ring-cyan-500 appearance-none text-sm"
                                                >
                                                    <option value="" class="dark:bg-[#1e293b]">全部显示 (未过滤)</option>
                                                    <option 
                                                        v-for="sg in mikanDetail?.subgroups || []" 
                                                        :key="sg.id" 
                                                        :value="sg.id"
                                                        class="dark:bg-[#1e293b]"
                                                    >
                                                        {{ sg.name }} {{ sg.latest_episode ? `[Ep ${sg.latest_episode}]` : '' }}
                                                    </option>
                                                </select>
                                                <div class="absolute right-3 top-3.5 pointer-events-none text-slate-400">
                                                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
                                                </div>
                                            </div>
                                            <p class="text-[10px] text-slate-400">选择字幕组以启用高级过滤。</p>
                                        </div>

                                        <div class="flex items-center justify-between p-4 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-100 dark:border-white/5">
                                            <div>
                                                <div class="font-bold text-sm text-slate-700 dark:text-gray-200">自动下载</div>
                                                <div class="text-[10px] text-slate-400">发现新剧集时自动添加任务</div>
                                            </div>
                                            <Switch
                                                v-model="dialogForm.auto_download"
                                                :class="dialogForm.auto_download ? 'bg-cyan-500' : 'bg-slate-200 dark:bg-slate-700'"
                                                class="relative inline-flex h-6 w-11 items-center rounded-full transition"
                                            >
                                                <span :class="dialogForm.auto_download ? 'translate-x-6' : 'translate-x-1'" class="inline-block h-4 w-4 transform rounded-full bg-white transition" />
                                            </Switch>
                                        </div>

                                    </div>

                                    <!-- Right: Filter & Preview (8 cols) -->
                                    <div class="lg:col-span-8 flex flex-col h-[520px] bg-slate-50 dark:bg-[#020617] rounded-3xl border border-slate-100 dark:border-white/5 overflow-hidden relative">
                                        
                                        <!-- Overlay for no subgroup -->
                                        <div v-if="!dialogForm.subgroup_id" class="absolute inset-0 z-10 bg-white/50 dark:bg-black/50 backdrop-blur-sm flex items-center justify-center">
                                            <div class="text-center p-6 pb-20">
                                                <div class="inline-flex justify-center items-center w-16 h-16 bg-white dark:bg-white/10 rounded-2xl mb-4 shadow-xl">
                                                    <svg class="w-8 h-8 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
                                                </div>
                                                <h3 class="text-xl font-black text-slate-800 dark:text-white">请先选择字幕组</h3>
                                                <p class="text-slate-500 font-medium">选择后即可配置过滤规则</p>
                                            </div>
                                        </div>

                                        <!-- Filter Area -->
                                        <div class="p-6 border-b border-slate-200 dark:border-white/5 bg-white dark:bg-[#0f172a]">
                                            <div class="flex justify-between items-center mb-4">
                                                <h4 class="font-black text-slate-700 dark:text-white flex items-center gap-2">
                                                    <svg class="w-5 h-5 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
                                                    智能过滤
                                                </h4>
                                                <div class="flex items-center gap-2">
                                                     <label class="text-[10px] uppercase font-bold text-slate-400">高级正则模式</label>
                                                     <Switch v-model="advancedMode" :class="advancedMode ? 'bg-indigo-500' : 'bg-slate-200 dark:bg-slate-700'" class="relative inline-flex h-5 w-9 items-center rounded-full transition">
                                                        <span :class="advancedMode ? 'translate-x-4' : 'translate-x-1'" class="inline-block h-3 w-3 transform rounded-full bg-white transition" />
                                                     </Switch>
                                                </div>
                                            </div>

                                            <!-- Smart Tags -->
                                            <div v-if="!advancedMode" class="space-y-3">
                                                <div class="flex flex-wrap gap-2">
                                                    <button 
                                                        v-for="tag in commonTags" 
                                                        :key="tag"
                                                        @click="toggleTag(tag)"
                                                        class="px-3 py-1.5 rounded-lg text-xs font-bold transition-all border"
                                                        :class="selectedTags.includes(tag) 
                                                            ? 'bg-cyan-500 text-white border-cyan-500 shadow-lg shadow-cyan-500/20' 
                                                            : 'bg-slate-50 dark:bg-white/5 text-slate-600 dark:text-slate-300 border-slate-100 dark:border-white/10 hover:border-cyan-300'"
                                                    >
                                                        {{ tag }}
                                                    </button>
                                                </div>
                                                <div v-if="commonTags.length === 0" class="text-xs text-slate-400 italic">
                                                    未能从视频标题分析出常用标签，请尝试切换字幕组或使用高级模式。
                                                </div>
                                                <p class="text-[10px] text-slate-400 mt-2">点击标签以组合筛选。只显示同时包含所有选中标签的视频。</p>
                                            </div>

                                            <!-- Raw Regex Input -->
                                            <div v-else class="space-y-2">
                                                <textarea 
                                                    v-model="dialogForm.filter_regex" 
                                                    rows="2"
                                                    placeholder="输入标准正则表达式..."
                                                    class="w-full p-3 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-xs font-mono text-slate-600 dark:text-slate-300 focus:ring-2 focus:ring-indigo-500"
                                                ></textarea>
                                                <p class="text-[10px] text-slate-400">支持 Python `re` 模块语法。留空则匹配所有。</p>
                                            </div>
                                        </div>

                                        <!-- Result Preview -->
                                        <div class="flex-1 overflow-hidden flex flex-col bg-slate-50 dark:bg-[#020617]/50">
                                            <div class="px-6 py-3 border-b border-slate-200 dark:border-white/5 flex justify-between items-center bg-slate-100/50 dark:bg-white/5">
                                                <h4 class="text-xs font-bold text-slate-500 uppercase">
                                                    预览结果
                                                    <span class="ml-2 px-2 py-0.5 rounded-full bg-slate-200 dark:bg-white/10 text-slate-700 dark:text-white">
                                                        {{ filteredPreviewVideos.length }} / {{ currentPreviewVideos.length }}
                                                    </span>
                                                </h4>
                                            </div>
                                            <div class="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar">
                                                 <div 
                                                    v-for="(vid, idx) in filteredPreviewVideos" 
                                                    :key="idx" 
                                                    class="bg-white dark:bg-[#0f172a] p-3 rounded-xl border border-slate-100 dark:border-white/5 hover:border-cyan-200 dark:hover:border-cyan-500/30 transition-colors group"
                                                >
                                                    <p class="text-xs font-mono text-slate-700 dark:text-slate-200 break-all leading-relaxed">
                                                        <!-- Highlight matching part? simplified for now -->
                                                        {{ vid.title }}
                                                    </p>
                                                    <div class="flex justify-between mt-2 opacity-60 text-[10px] font-bold">
                                                        <span class="bg-slate-100 dark:bg-white/10 px-1.5 py-0.5 rounded text-slate-500 dark:text-slate-400">{{ vid.size }}</span>
                                                        <span>{{ vid.pub_date }}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- Footer -->
                            <div class="px-8 py-5 border-t border-slate-100 dark:border-white/5 bg-slate-50 dark:bg-[#0f172a] flex justify-between items-center">
                                <div class="text-xs text-slate-500 dark:text-slate-400 max-w-md truncate flex items-center gap-2">
                                    <svg v-if="dialogForm.subgroup_id" class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>
                                    <span v-if="dialogForm.subgroup_id" class="font-mono">{{ dialogForm.save_path }}</span>
                                </div>
                                <div class="flex gap-3">
                                    <button @click="showDialog = false" class="px-6 py-2.5 rounded-xl font-bold text-slate-500 hover:bg-slate-200 dark:hover:bg-white/10 transition-colors">
                                        取消
                                    </button>
                                    <button @click="saveSubscription" class="px-6 py-2.5 rounded-xl bg-cyan-500 text-white font-bold shadow-lg shadow-cyan-500/30 hover:bg-cyan-400 hover:scale-105 active:scale-95 transition-all">
                                        {{ editingSubscription ? '保存订阅' : '确认订阅' }}
                                    </button>
                                </div>
                            </div>
                        </DialogPanel>
                    </TransitionChild>
                </div>
            </div>
        </Dialog>
    </TransitionRoot>

    <!-- RSS Items Dialog -->
    <TransitionRoot appear :show="showItemsDialog" as="template">
        <Dialog as="div" @close="showItemsDialog = false" class="relative z-50">
            <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm" />
            <div class="fixed inset-0 overflow-y-auto">
                <div class="flex min-h-full items-center justify-center p-4">
                    <DialogPanel class="w-full max-w-2xl transform overflow-hidden rounded-3xl bg-white dark:bg-[#0f172a] border border-slate-100 dark:border-white/10 p-6 shadow-2xl">
                        <DialogTitle class="text-xl font-black mb-4 dark:text-white">{{ currentSubTitle }} - 更新记录</DialogTitle>
                        <div class="max-h-[60vh] overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                            <div v-if="currentRSSItems.length === 0" class="text-center text-slate-400 py-8">暂无记录</div>
                            <div v-for="item in currentRSSItems" :key="item.id" class="p-3 rounded-xl bg-slate-50 dark:bg-white/5 flex items-start gap-3">
                                <div class="mt-1">
                                    <span v-if="item.downloaded" class="text-emerald-500 text-xs font-bold border border-emerald-500/20 bg-emerald-500/10 px-1.5 py-0.5 rounded">已下载</span>
                                    <span v-else class="text-slate-400 text-xs font-bold border border-slate-200 dark:border-white/10 px-1.5 py-0.5 rounded">未下载</span>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <p class="text-sm font-bold text-slate-700 dark:text-slate-200 line-clamp-2">{{ item.title }}</p>
                                    <p class="text-xs text-slate-400 mt-1">{{ new Date(item.pub_date).toLocaleString() }}</p>
                                </div>
                            </div>
                        </div>
                    </DialogPanel>
                </div>
            </div>
        </Dialog>
    </TransitionRoot>

    <BaseConfirmDialog 
        :show="showConfirm" 
        :message="confirmMsg" 
        @update:show="showConfirm = $event" 
        @confirm="confirmAction && confirmAction(); showConfirm = false" 
        title="确认操作"
    >
        <div class="mt-4 p-4 bg-slate-50 dark:bg-white/5 rounded-xl border border-slate-100 dark:border-white/5">
             <div class="flex items-start gap-3">
                 <input type="checkbox" id="delFiles" v-model="deleteLocalFiles" class="mt-1 w-4 h-4 text-rose-500 rounded border-slate-300 focus:ring-rose-500 cursor-pointer">
                 <div class="flex-1">
                     <label for="delFiles" class="font-bold text-slate-700 dark:text-slate-200 text-sm select-none cursor-pointer">同时删除本地文件</label>
                     <p v-if="editingSubscription" class="text-xs text-slate-400 mt-1 font-mono break-all leading-relaxed">
                         将连同任务及文件一起删除 <br>
                         路径: {{ editingSubscription.save_path }}
                     </p>
                 </div>
             </div>
        </div>
    </BaseConfirmDialog>
</div>
</template>
