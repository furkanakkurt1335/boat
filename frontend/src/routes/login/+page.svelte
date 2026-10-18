<script lang="ts">
	import { goto } from '$app/navigation';
	import { login } from '$stores/auth';
	import { ApiError } from '$api/client';
	import Button from '$components/common/Button.svelte';
	import Input from '$components/common/Input.svelte';

	let username = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		loading = true;
		try {
			await login(username, password);
			await goto('/dashboard');
		} catch (err) {
			error = err instanceof ApiError ? err.detail : 'Login failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-muted">
	<div class="w-full max-w-sm space-y-6 rounded-lg bg-background p-8 shadow-lg">
		<div class="text-center">
			<h1 class="text-2xl font-bold">BoAT</h1>
			<p class="text-sm text-muted-foreground">Boğaziçi University Annotation Tool</p>
		</div>

		{#if error}
			<div id="login-error" class="rounded-md bg-destructive/10 p-3 text-sm text-destructive" role="alert">{error}</div>
		{/if}

		<form onsubmit={handleSubmit} class="space-y-4">
			<div class="space-y-2">
				<label for="username" class="text-sm font-medium">Username</label>
				<Input id="username" bind:value={username} required placeholder="Username" aria-invalid={!!error} aria-describedby={error ? 'login-error' : undefined} />
			</div>
			<div class="space-y-2">
				<label for="password" class="text-sm font-medium">Password</label>
				<Input id="password" type="password" bind:value={password} required placeholder="Password" aria-invalid={!!error} aria-describedby={error ? 'login-error' : undefined} />
			</div>
			<Button type="submit" class="w-full" disabled={loading}>
				{loading ? 'Signing in...' : 'Sign in'}
			</Button>
		</form>

		<p class="text-center text-sm text-muted-foreground">
			Don't have an account?
			<a href="/register" class="text-primary hover:underline">Register</a>
		</p>
	</div>
</div>
