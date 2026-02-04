import request from '@/utils/request'

// ========== New Key-Value Settings API ==========

/**
 * Get all settings grouped by category
 * Returns: { "app": [...], "llm": [...], "tmdb": [...] }
 */
export function getAllSettings() {
    return request({
        url: '/settings',
        method: 'get'
    })
}

/**
 * Get settings for a specific category
 * @param {string} category - "app", "llm", or "tmdb"
 */
export function getSettingsByCategory(category) {
    return request({
        url: `/settings/${category}`,
        method: 'get'
    })
}

/**
 * Batch update settings
 * @param {Object} updates - { "app.language": "zh_CN", "llm.api_key": "..." }
 */
export function updateSettings(updates) {
    return request({
        url: '/settings',
        method: 'put',
        data: { updates }
    })
}

// ========== LLM Test Connection ==========

/**
 * Test LLM connection with provided config
 * @param {Object} config - { provider, api_key, base_url, model }
 */
export function testLLMConnection(config) {
    return request({
        url: '/settings/llm/test',
        method: 'post',
        data: config
    })
}

// ========== Legacy API (Deprecated) ==========

export function getAppSettings() {
    return request({
        url: '/settings/legacy/app',
        method: 'get'
    })
}

export function updateAppSettings(data) {
    return request({
        url: '/settings/legacy/app',
        method: 'post',
        data
    })
}

// ========== LLM Presets API ==========

// ========== LLM Presets API ==========

export function getPresets() {
    return request({
        url: '/settings/presets',
        method: 'get'
    })
}

export function createPreset(data) {
    return request({
        url: '/settings/presets',
        method: 'post',
        data
    })
}

export function updatePreset(id, data) {
    return request({
        url: `/settings/presets/${id}`,
        method: 'put',
        data
    })
}

export function deletePreset(id) {
    return request({
        url: `/settings/presets/${id}`,
        method: 'delete'
    })
}

export function testConnection(data) {
    return request({
        url: '/settings/llm/test',
        method: 'post',
        data
    })
}

export function sendTestEmail() {
    return request({
        url: '/settings/notification/test-email',
        method: 'post'
    })
}

