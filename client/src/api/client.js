import axios from 'axios';

const baseURL = process.env.REACT_APP_API_BASE_URL || '/api';

export const api = axios.create({ baseURL });

export function setAuthToken(token) {
  if (token) {
    api.defaults.headers.common['x-auth-token'] = token;
  } else {
    delete api.defaults.headers.common['x-auth-token'];
  }
}

