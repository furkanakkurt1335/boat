<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { toast } from '$stores/toast';

	function handleKeydown(e: KeyboardEvent) {
		// Ctrl+O — open file
		if (e.ctrlKey && e.key === 'o') {
			e.preventDefault();
			openFile();
		}
		// Ctrl+S — save
		if (e.ctrlKey && !e.shiftKey && e.key === 's') {
			e.preventDefault();
			window.dispatchEvent(new CustomEvent('boat:save'));
		}
		// Ctrl+Shift+S — save as
		if (e.ctrlKey && e.shiftKey && e.key === 'S') {
			e.preventDefault();
			window.dispatchEvent(new CustomEvent('boat:save-as'));
		}
	}

	async function openFile() {
		try {
			const { invoke } = await import('@tauri-apps/api/core');
			await invoke('open_file');
			// Navigation will be handled by the caller listening to events
			window.dispatchEvent(new CustomEvent('boat:file-opened'));
		} catch (err) {
			if (err !== 'No file selected') {
				toast.error(String(err));
			}
		}
	}

	onMount(() => {
		window.addEventListener('keydown', handleKeydown);
	});

	onDestroy(() => {
		window.removeEventListener('keydown', handleKeydown);
	});
</script>
