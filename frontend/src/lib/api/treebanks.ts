import { get } from 'svelte/store';
import { api, getBaseUrl, TOKEN_KEY } from './client';
import { appMode } from '$stores/mode';
import type { TreebankRead, TreebankWithProgress, AgreementResponse, TreebankStats } from './types';

export function listTreebanks() {
	return api.get<TreebankWithProgress[]>('/treebanks');
}

export function getTreebank(id: number) {
	return api.get<TreebankRead>(`/treebanks/${id}`);
}

export function getTreebankByTitle(title: string) {
	return api.get<TreebankRead>(`/treebanks/by-title/${encodeURIComponent(title)}`);
}

export function createTreebank(title: string, language: string) {
	return api.post<TreebankRead>('/treebanks', { title, language });
}

export function deleteTreebank(id: number) {
	return api.del(`/treebanks/${id}`);
}

export function uploadConllu(id: number, file: File) {
	const formData = new FormData();
	formData.append('file', file);
	return api.upload<{ sentences_created: number }>(`/treebanks/${id}/upload`, formData);
}

export async function exportConllu(id: number) {
	// In offline mode, use Tauri save-as dialog
	if (get(appMode) === 'offline') {
		const { invoke } = await import('@tauri-apps/api/core');
		await invoke('save_file_as');
		return;
	}

	const base = getBaseUrl();
	const token = typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
	const headers: Record<string, string> = {};
	if (token) headers['Authorization'] = `Bearer ${token}`;
	const res = await fetch(`${base}/treebanks/${id}/export`, { headers });
	if (!res.ok) throw new Error('Export failed');
	const blob = await res.blob();
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = `treebank-${id}.conllu`;
	a.click();
	URL.revokeObjectURL(url);
}

export function getTreebankStats(id: number) {
	return api.get<TreebankStats>(`/treebanks/${id}/stats`);
}

export function getAgreement(id: number) {
	return api.get<AgreementResponse>(`/treebanks/${id}/agreement`);
}

export function getLanguages() {
	return api.get<Record<string, string>>('/treebanks/languages');
}
