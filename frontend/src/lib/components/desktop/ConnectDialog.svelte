<script lang="ts">
	import { appMode, serverUrl } from '$stores/mode';
	import { login } from '$stores/auth';
	import { toast } from '$stores/toast';
	import { goto } from '$app/navigation';
	import Modal from '$components/common/Modal.svelte';
	import Button from '$components/common/Button.svelte';

	let { open = $bindable(false) } = $props();

	let url = $state('http://localhost:8000');
	let username = $state('');
	let password = $state('');
	let connecting = $state(false);
	let testing = $state(false);
	let testResult = $state<'ok' | 'fail' | null>(null);

	async function testConnection() {
		testing = true;
		testResult = null;
		try {
			const res = await fetch(`${url}/health`);
			testResult = res.ok ? 'ok' : 'fail';
		} catch {
			testResult = 'fail';
		} finally {
			testing = false;
		}
	}

	async function handleConnect() {
		connecting = true;
		try {
			const res = await fetch(`${url}/health`);
			if (!res.ok) throw new Error('Server not reachable');

			serverUrl.set(url);
			appMode.set('connected');
			await login(username, password);
			open = false;
			await goto('/dashboard');
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Connection failed');
		} finally {
			connecting = false;
		}
	}
</script>

<Modal {open} onclose={() => (open = false)} title="Connect to Server">
	<form onsubmit={(e) => { e.preventDefault(); handleConnect(); }} class="space-y-4">
		<div>
			<label for="connect-url" class="block text-sm font-medium mb-1">Server URL</label>
			<div class="flex gap-2">
				<input
					id="connect-url"
					type="url"
					bind:value={url}
					class="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
					placeholder="http://localhost:8000"
				/>
				<button
					type="button"
					onclick={testConnection}
					disabled={testing}
					class="rounded-md border border-border px-3 py-2 text-sm text-muted-foreground hover:text-foreground cursor-pointer"
				>
					{testing ? 'Testing...' : 'Test'}
				</button>
			</div>
			{#if testResult === 'ok'}
				<p class="mt-1 text-xs text-green-600">Server reachable</p>
			{:else if testResult === 'fail'}
				<p class="mt-1 text-xs text-destructive">Server not reachable</p>
			{/if}
		</div>
		<div>
			<label for="connect-username" class="block text-sm font-medium mb-1">Username</label>
			<input
				id="connect-username"
				type="text"
				bind:value={username}
				class="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
			/>
		</div>
		<div>
			<label for="connect-password" class="block text-sm font-medium mb-1">Password</label>
			<input
				id="connect-password"
				type="password"
				bind:value={password}
				class="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
			/>
		</div>
		<div class="flex justify-end gap-2">
			<button
				type="button"
				onclick={() => (open = false)}
				class="rounded-md border border-border px-4 py-2 text-sm cursor-pointer"
			>Cancel</button>
			<Button type="submit" disabled={connecting || !username || !password}>
				{connecting ? 'Connecting...' : 'Connect'}
			</Button>
		</div>
	</form>
</Modal>
