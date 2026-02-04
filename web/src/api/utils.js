import request from '@/utils/request'

/**
 * Get initial character for text
 * @param {string} text 
 */
export function getTextInitial(text) {
    return request({
        url: '/utils/initial',
        method: 'post',
        data: { text }
    })
}
