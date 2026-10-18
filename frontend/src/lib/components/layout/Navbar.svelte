<script lang="ts">
	import { user, logout } from '$stores/auth';
	import { appMode, serverUrl } from '$stores/mode';
	import { theme } from '$stores/theme';
	import { toast } from '$stores/toast';
	import { goto } from '$app/navigation';

	async function handleLogout() {
		logout();
		if ($appMode !== 'web') {
			appMode.set('offline');
			serverUrl.set('');
			await goto('/desktop');
		} else {
			await goto('/login');
		}
	}

	let currentTheme = $state<string>('system');
	theme.subscribe((v) => (currentTheme = v));

	function cycleTheme() {
		const order = ['light', 'dark', 'system'] as const;
		type T = (typeof order)[number];
		const idx = order.indexOf(currentTheme as T);
		const next = order[(idx + 1) % order.length];
		theme.set(next);
	}

	const themeIcon = $derived(
		currentTheme === 'light' ? '\u2600' : currentTheme === 'dark' ? '\u263E' : '\u25D0'
	);

	async function handleOpen() {
		try {
			const { invoke } = await import('@tauri-apps/api/core');
			const result = await invoke<{ title: string }>('open_file');
			await goto(`/treebanks/${encodeURIComponent(result.title)}`);
		} catch (err) {
			if (err !== 'No file selected') {
				toast.error(String(err));
			}
		}
	}

	async function handleSave() {
		window.dispatchEvent(new CustomEvent('boat:save'));
	}

	async function handleSaveAs() {
		window.dispatchEvent(new CustomEvent('boat:save-as'));
	}
</script>

<nav class="border-b border-border bg-background">
	<div class="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
		<div class="flex items-center gap-6">
			{#if $appMode === 'offline'}
				<a href="/desktop" class="text-lg font-bold tracking-tight font-brand">BoAT</a>
				<div class="hidden items-center gap-4 text-sm md:flex">
					<button onclick={handleOpen} class="text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
						Open File
					</button>
					<button onclick={handleSave} class="text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
						Save
					</button>
					<button onclick={handleSaveAs} class="text-muted-foreground hover:text-foreground transition-colors cursor-pointer">
						Save As
					</button>
				</div>
			{:else}
				<a href="/dashboard" class="text-lg font-bold tracking-tight font-brand">BoAT</a>
				<div class="hidden items-center gap-4 text-sm md:flex">
					<a href="/treebanks" class="text-muted-foreground hover:text-foreground transition-colors">
						Treebanks
					</a>
					<a href="/annotations/mine" class="text-muted-foreground hover:text-foreground transition-colors">
						My Annotations
					</a>
					<a href="/search" class="text-muted-foreground hover:text-foreground transition-colors">
						Search
					</a>
					<a href="/rewrite" class="text-muted-foreground hover:text-foreground transition-colors">
						Rewrite
					</a>
					{#if $user?.is_admin}
						<a href="/admin" class="text-muted-foreground hover:text-foreground transition-colors">
							Admin
						</a>
					{/if}
				</div>
			{/if}
		</div>
		<div class="flex items-center gap-4 text-sm">
			{#if $appMode === 'offline'}
				<span class="rounded-full bg-yellow-100 px-2 py-0.5 text-xs text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">Offline</span>
			{:else if $appMode === 'connected'}
				<span class="rounded-full bg-green-100 px-2 py-0.5 text-xs text-green-800 dark:bg-green-900 dark:text-green-200" title={$serverUrl}>Connected</span>
			{/if}
			<button
				onclick={cycleTheme}
				class="text-muted-foreground hover:text-foreground transition-colors cursor-pointer text-base"
				title="Toggle theme (light/dark/system)"
			>{themeIcon}</button>
			{#if $user}
				<a href="/preferences" class="text-muted-foreground hover:text-foreground transition-colors">
					{$user.username}
				</a>
				<button
					onclick={handleLogout}
					class="text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
				>
					{$appMode === 'connected' ? 'Disconnect' : 'Logout'}
				</button>
			{/if}
		</div>
	</div>
</nav>
