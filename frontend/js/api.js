/**
 * API client module for REST endpoints.
 * Handles uniform error extraction and injects X-Client-Id header.
 */

// Generate a random client ID per browser tab to avoid echo redraws
export const CLIENT_ID = (() => {
  const key = 'packing_app_client_id';
  let id = sessionStorage.getItem(key);
  if (!id) {
    id = 'tab_' + Math.random().toString(36).substring(2, 10);
    sessionStorage.setItem(key, id);
  }
  return id;
})();

async function request(url, options = {}) {
  const headers = {
    'Accept': 'application/json',
    'X-Client-Id': CLIENT_ID,
    ...options.headers,
  };

  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  const response = await fetch(url, { ...options, headers });

  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get('content-type') || '';
  let data = null;
  if (contentType.includes('application/json')) {
    data = await response.json();
  }

  if (!response.ok) {
    const errorMsg = data?.error?.message || `שגיאה (${response.status})`;
    const error = new Error(errorMsg);
    error.status = response.status;
    error.data = data?.error;
    throw error;
  }

  return data;
}

export const api = {
  // Health
  getHealth: () => request('/api/health'),

  // Family Members
  getMembers: () => request('/api/members'),
  createMember: (data) => request('/api/members', { method: 'POST', body: data }),
  updateMember: (id, data) => request(`/api/members/${id}`, { method: 'PATCH', body: data }),
  deleteMember: (id) => request(`/api/members/${id}`, { method: 'DELETE' }),

  // Trips
  getTrips: () => request('/api/trips'),
  getTrip: (id) => request(`/api/trips/${id}`),
  createTrip: (data) => request('/api/trips', { method: 'POST', body: data }),
  updateTrip: (id, data) => request(`/api/trips/${id}`, { method: 'PATCH', body: data }),
  deleteTrip: (id) => request(`/api/trips/${id}`, { method: 'DELETE' }),
  cloneTrip: (id, data) => request(`/api/trips/${id}/clone`, { method: 'POST', body: data }),
  resetTrip: (id) => request(`/api/trips/${id}/reset`, { method: 'POST' }),

  // Categories
  createCategory: (tripId, data) => request(`/api/trips/${tripId}/categories`, { method: 'POST', body: data }),
  updateCategory: (id, data) => request(`/api/categories/${id}`, { method: 'PATCH', body: data }),
  deleteCategory: (id) => request(`/api/categories/${id}`, { method: 'DELETE' }),
  packAllCategory: (id, packed = true) => request(`/api/categories/${id}/pack-all`, { method: 'POST', body: { packed } }),

  // Items
  createItem: (categoryId, data) => request(`/api/categories/${categoryId}/items`, { method: 'POST', body: data }),
  updateItem: (id, data) => request(`/api/items/${id}`, { method: 'PATCH', body: data }),
  deleteItem: (id) => request(`/api/items/${id}`, { method: 'DELETE' }),

  // Import / Export
  exportAllUrl: () => '/api/export',
  exportTripUrl: (id) => `/api/trips/${id}/export`,
  importData: (doc) => request('/api/import', { method: 'POST', body: doc }),
};
