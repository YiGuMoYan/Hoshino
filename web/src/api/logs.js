import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
});

export const getLogs = async (params) => {
  const response = await api.get('/logs', { params });
  return response.data;
};
