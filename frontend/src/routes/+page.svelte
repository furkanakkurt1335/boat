<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isAuthenticated, isLoading } from '$stores/auth';
	import { appMode } from '$stores/mode';

	onMount(() => {
		const unsubLoading = isLoading.subscribe((loading) => {
			if (loading) return;
			// In Tauri offline mode, go to desktop landing
			if ($appMode === 'offline') {
				goto('/desktop');
				return;
			}
			const unsub = isAuthenticated.subscribe((authed) => {
				goto(authed ? '/dashboard' : '/login');
				unsub();
			});
		});
		return unsubLoading;
	});
</script>
