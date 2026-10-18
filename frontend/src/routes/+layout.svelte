<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { initialize, isAuthenticated, isLoading } from '$stores/auth';
	import { appMode } from '$stores/mode';
	import { theme } from '$stores/theme';
	import Navbar from '$components/layout/Navbar.svelte';
	import DesktopShortcuts from '$components/desktop/DesktopShortcuts.svelte';
	import Toast from '$components/common/Toast.svelte';

	const isTauriMode = $derived($appMode !== 'web');

	let { children } = $props();

	const publicRoutes = ['/login', '/register', '/desktop'];

	onMount(async () => {
		theme.initialize();
		await initialize();
	});

	$effect(() => {
		if ($isLoading) return;
		const path = page.url.pathname;
		// In offline mode, skip login redirect
		if ($appMode === 'offline') return;
		if (!$isAuthenticated && !publicRoutes.includes(path)) {
			goto('/login');
		}
	});

	const showNavbar = $derived(
		$isAuthenticated && !page.url.pathname.startsWith('/annotate/') && !page.url.pathname.startsWith('/desktop')
	);
</script>

<svelte:head>
	<title>BoAT</title>
</svelte:head>

{#if $isLoading}
	<div class="flex h-screen items-center justify-center">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
	</div>
{:else}
	{#if isTauriMode}
		<DesktopShortcuts />
	{/if}
	{#if showNavbar}
		<Navbar />
	{/if}
	{@render children()}
{/if}
<Toast />
