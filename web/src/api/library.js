import request from '@/utils/request'

const API_BASE = '/api'

export function scanLibrary() {
  return request({
    url: '/library/scan',
    method: 'post'
  })
}

export function getLibraryItems() {
  return request({
    url: '/library/items',
    method: 'get'
  })
}

export function getLibraryItemEpisodes(itemId) {
  return request({
    url: `/library/items/${itemId}/episodes`,
    method: 'get'
  })
}

export function deleteLibraryItem(itemId, params) {
  return request({
    url: `/library/items/${itemId}`,
    method: 'delete',
    params
  })
}

export function getLibraryImage(encodedPath) {
  return `${API_BASE}/library/image/${encodedPath}`
}
