<script lang="ts">
	import { goto } from '$app/navigation';
	import { appMode, serverUrl } from '$stores/mode';
	import { login } from '$stores/auth';
	import { toast } from '$stores/toast';
	import { theme } from '$stores/theme';
	import Button from '$components/common/Button.svelte';

	let recentFiles = $state<Array<{ title: string; path: string }>>(loadRecent());
	let showConnect = $state(false);
	let connectUrl = $state('http://localhost:8000');
	let connectUsername = $state('');
	let connectPassword = $state('');
	let connecting = $state(false);

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

	function loadRecent(): Array<{ title: string; path: string }> {
		try {
			const raw = localStorage.getItem('boat-recent-files');
			return raw ? JSON.parse(raw) : [];
		} catch {
			return [];
		}
	}

	function saveRecent(files: Array<{ title: string; path: string }>) {
		localStorage.setItem('boat-recent-files', JSON.stringify(files.slice(0, 10)));
	}

	async function openFile() {
		try {
			const { invoke } = await import('@tauri-apps/api/core');
			const result = await invoke<{ title: string; path: string; sentence_count: number }>('open_file');

			// Add to recent files
			recentFiles = [
				{ title: result.title, path: result.path },
				...recentFiles.filter((f) => f.path !== result.path)
			].slice(0, 10);
			saveRecent(recentFiles);

			await goto(`/treebanks/${encodeURIComponent(result.title)}`);
		} catch (err) {
			if (err !== 'No file selected') {
				toast.error(String(err));
			}
		}
	}

	async function handleConnect() {
		connecting = true;
		try {
			// Test connection
			const res = await fetch(`${connectUrl}/health`);
			if (!res.ok) throw new Error('Server not reachable');

			serverUrl.set(connectUrl);
			appMode.set('connected');
			await login(connectUsername, connectPassword);
			await goto('/dashboard');
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Connection failed');
		} finally {
			connecting = false;
		}
	}
</script>

<div class="flex h-screen flex-col bg-background text-foreground">
	<!-- Minimal top bar -->
	<div class="flex h-12 items-center justify-between border-b border-border px-4">
		<span class="text-lg font-bold tracking-tight font-brand">BoAT</span>
		<div class="flex items-center gap-3 text-sm">
			<span class="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">Offline</span>
			<button
				onclick={cycleTheme}
				class="text-muted-foreground hover:text-foreground transition-colors cursor-pointer text-base"
				title="Toggle theme"
			>{themeIcon}</button>
		</div>
	</div>

	<!-- Main content -->
	<div class="flex flex-1 items-center justify-center">
		<div class="w-full max-w-lg space-y-8 px-6">
			<div class="text-center">
				<h1 class="text-3xl font-bold tracking-tight font-brand">BoAT Desktop</h1>
				<p class="mt-2 text-sm text-muted-foreground">Open a CoNLL-U file to start annotating, or connect to a server.</p>
			</div>

			<!-- Actions -->
			<div class="space-y-3">
				<button
					onclick={openFile}
					class="flex w-full items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border bg-muted/30 px-4 py-6 text-sm font-medium transition-colors hover:border-primary hover:bg-primary/5 cursor-pointer"
				>
					<span class="text-lg">+</span>
					Open CoNLL-U file
				</button>

				<button
					onclick={() => (showConnect = !showConnect)}
					class="flex w-full items-center justify-center gap-2 rounded-lg border border-border px-4 py-3 text-sm text-muted-foreground transition-colors hover:text-foreground hover:border-foreground/20 cursor-pointer"
				>
					Connect to server
				</button>
			</div>

			<!-- Connect form (toggled) -->
			{#if showConnect}
				<form onsubmit={(e) => { e.preventDefault(); handleConnect(); }} class="space-y-3 rounded-lg border border-border p-4">
					<div>
						<label for="server-url" class="block text-xs font-medium text-muted-foreground mb-1">Server URL</label>
						<input
							id="server-url"
							type="url"
							bind:value={connectUrl}
							class="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
							placeholder="http://localhost:8000"
						/>
					</div>
					<div class="grid grid-cols-2 gap-3">
						<div>
							<label for="username" class="block text-xs font-medium text-muted-foreground mb-1">Username</label>
							<input
								id="username"
								type="text"
								bind:value={connectUsername}
								class="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
							/>
						</div>
						<div>
							<label for="password" class="block text-xs font-medium text-muted-foreground mb-1">Password</label>
							<input
								id="password"
								type="password"
								bind:value={connectPassword}
								class="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
							/>
						</div>
					</div>
					<Button type="submit" disabled={connecting || !connectUsername || !connectPassword}>
						{connecting ? 'Connecting...' : 'Connect'}
					</Button>
				</form>
			{/if}

			<!-- Recent files -->
			{#if recentFiles.length > 0}
				<div>
					<h2 class="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Recent Files</h2>
					<div class="space-y-1">
						{#each recentFiles as file}
							<button
								onclick={() => {
									// TODO: open specific file path directly
									openFile();
								}}
								class="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-muted cursor-pointer"
							>
								<span class="truncate font-medium">{file.title}</span>
								<span class="ml-auto truncate text-xs text-muted-foreground max-w-48">{file.path}</span>
							</button>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>
