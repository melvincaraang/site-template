const API_BASE = '/api';

async function request(path: string, options: RequestInit = {}) {
	const res = await fetch(`${API_BASE}${path}`, {
		credentials: 'include',
		headers: { 'Content-Type': 'application/json', ...options.headers },
		...options
	});
	const data = await res.json();
	if (!res.ok) throw { status: res.status, ...data };
	return data;
}

export const api = {
	verify: (body: { code?: string; token?: string; admin?: boolean }) =>
		request('/verify', { method: 'POST', body: JSON.stringify(body) }),

	getSession: () => request('/session'),

	logout: () => request('/logout', { method: 'POST' }),

	getMedia: () => request('/media'),

	getMessages: () => request('/messages'),

	postMessage: (author: string, text: string) =>
		request('/messages', { method: 'POST', body: JSON.stringify({ author, text }) }),

	getTokens: () => request('/admin/tokens'),

	createToken: (label: string, expiresInDays: number) =>
		request('/admin/tokens', {
			method: 'POST',
			body: JSON.stringify({ label, expiresInDays })
		}),

	deleteToken: (uuid: string) => request(`/admin/tokens/${uuid}`, { method: 'DELETE' }),

	getUploadUrl: (filename: string, contentType: string) =>
		request('/admin/media/upload-url', {
			method: 'POST',
			body: JSON.stringify({ filename, contentType })
		}),

	saveMedia: (s3Key: string, type: string, caption: string) =>
		request('/admin/media', {
			method: 'POST',
			body: JSON.stringify({ s3Key, type, caption })
		}),

	deleteMedia: (id: string) => request(`/admin/media/${id}`, { method: 'DELETE' }),

	updateMedia: (id: string, updates: { caption?: string; order?: number }) =>
		request(`/admin/media/${id}`, { method: 'PUT', body: JSON.stringify(updates) })
};
