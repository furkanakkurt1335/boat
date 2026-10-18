import { writable, derived, get } from 'svelte/store';
import type { UserRead } from '$api/types';
import * as authApi from '$api/auth';
import { TOKEN_KEY } from '$api/client';
import { appMode } from '$stores/mode';

export const user = writable<UserRead | null>(null);
export const isAuthenticated = derived(user, ($user) => $user !== null);
export const isLoading = writable(true);

const OFFLINE_USER: UserRead = {
	id: 0,
	username: 'local',
	email: '',
	first_name: 'Local',
	last_name: 'User',
	is_active: true,
	is_admin: false,
	preferences: {
		graph_preference: 1,
		error_condition: false,
		current_columns: ['ID', 'FORM', 'LEMMA', 'UPOS', 'XPOS', 'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC']
	}
};

export async function initialize() {
	// In offline (Tauri) mode, skip server auth entirely
	if (get(appMode) === 'offline') {
		user.set(OFFLINE_USER);
		isLoading.set(false);
		return;
	}

	const token = localStorage.getItem(TOKEN_KEY);
	if (!token) {
		isLoading.set(false);
		return;
	}
	try {
		const me = await authApi.getMe();
		user.set(me);
	} catch {
		localStorage.removeItem(TOKEN_KEY);
	} finally {
		isLoading.set(false);
	}
}

export async function login(username: string, password: string) {
	const { access_token } = await authApi.login(username, password);
	localStorage.setItem(TOKEN_KEY, access_token);
	const me = await authApi.getMe();
	user.set(me);
}

export async function register(data: {
	username: string;
	email: string;
	password: string;
	first_name: string;
	last_name: string;
}): Promise<UserRead> {
	const newUser = await authApi.register(data);
	if (newUser.is_active) {
		await login(data.username, data.password);
	}
	return newUser;
}

export function logout() {
	localStorage.removeItem(TOKEN_KEY);
	user.set(null);
}

export async function updatePreferences(prefs: Record<string, unknown>) {
	const updated = await authApi.updateMe({ preferences: prefs });
	user.set(updated);
}
