import { writable, derived } from 'svelte/store';

export interface Toast {
	id: number;
	message: string;
	variant: 'success' | 'error' | 'info';
}

let nextId = 0;
const _toasts = writable<Toast[]>([]);

export const toasts = derived(_toasts, ($t) => $t);

function dismiss(id: number) {
	_toasts.update((t) => t.filter((toast) => toast.id !== id));
}

function push(message: string, variant: Toast['variant'], duration: number) {
	const id = nextId++;
	_toasts.update((t) => [...t, { id, message, variant }]);
	setTimeout(() => dismiss(id), duration);
	return id;
}

export const toast = {
	success: (message: string) => push(message, 'success', 3000),
	error: (message: string) => push(message, 'error', 5000),
	info: (message: string) => push(message, 'info', 3000),
	dismiss,
};
