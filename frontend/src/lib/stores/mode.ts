import { writable, derived } from 'svelte/store';

export type AppMode = 'web' | 'offline' | 'connected';

function detectInitialMode(): AppMode {
	if (typeof window !== 'undefined' && (window as unknown as Record<string, unknown>).isTauri) {
		return 'offline';
	}
	return 'web';
}

export const appMode = writable<AppMode>(detectInitialMode());
export const serverUrl = writable<string>('');

export const isOffline = derived(appMode, ($m) => $m === 'offline');
export const isConnected = derived(appMode, ($m) => $m === 'connected');
export const isWeb = derived(appMode, ($m) => $m === 'web');
export const isTauri = derived(appMode, ($m) => $m !== 'web');
