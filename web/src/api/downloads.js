import request from '@/utils/request';

export const listDownloads = () => request.get('/downloads/list');

export const addMagnetTask = (data) => request.post('/downloads/add/magnet', data);
// data: { url, save_path, extra_vars: { series_name, season, ... } }

export const testConnection = (config) => request.post('/downloads/test-connection', config);


export const previewTorrent = (formData) => request.post('/downloads/preview', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});

export const addTorrentTask = (formData) => request.post('/downloads/add/torrent', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
});

export const retryTask = (infoHash) => request.post(`/downloads/retry/${infoHash}`);

export const deleteTask = (infoHash, deleteFiles = false) => request.delete(`/downloads/delete/${infoHash}`, { params: { delete_files: deleteFiles } });
