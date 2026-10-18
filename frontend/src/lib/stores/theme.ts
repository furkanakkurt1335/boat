import { writable } from 'svelte/store';

type Theme = 'light' | 'dark' | 'system';

function createThemeStore() {
	const stored = typeof window !== 'undefined' ? localStorage.getItem('theme') as Theme : null;
	const { subscribe, set } = writable<Theme>(stored ?? 'system');

	function apply(theme: Theme) {
		if (typeof window === 'undefined') return;
		const isDark =
			theme === 'dark' ||
			(theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
		document.documentElement.classList.toggle('dark', isDark);
	}

	return {
		subscribe,
		set(theme: Theme) {
			set(theme);
			if (typeof window !== 'undefined') {
				localStorage.setItem('theme', theme);
			}
			apply(theme);
		},
		initialize() {
			const saved = typeof window !== 'undefined' ? localStorage.getItem('theme') as Theme : null;
			const t = saved ?? 'system';
			set(t);
			apply(t);
		}
	};
}

export const theme = createThemeStore();
