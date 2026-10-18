<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { register } from '$stores/auth';
	import { api, ApiError } from '$api/client';
	import Button from '$components/common/Button.svelte';
	import Input from '$components/common/Input.svelte';

	let username = $state('');
	let email = $state('');
	let firstName = $state('');
	let lastName = $state('');
	let password = $state('');
	let password2 = $state('');
	let error = $state('');
	let loading = $state(false);
	let registrationMode = $state<string>('approval');
	let registered = $state(false);

	onMount(async () => {
		try {
			const res = await api.get<{ mode: string }>('/auth/registration-mode');
			registrationMode = res.mode;
		} catch {
			// Default to approval if endpoint fails
		}
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = '';
		if (password !== password2) {
			error = 'Passwords do not match';
			return;
		}
		loading = true;
		try {
			const newUser = await register({
				username,
				email,
				password,
				first_name: firstName,
				last_name: lastName
			});
			if (newUser.is_active) {
				await goto('/dashboard');
			} else {
				registered = true;
			}
		} catch (err) {
			error = err instanceof ApiError ? err.detail : 'Registration failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-muted">
	<div class="w-full max-w-sm space-y-6 rounded-lg bg-background p-8 shadow-lg">
		{#if registrationMode === 'closed'}
			<div class="text-center">
				<h1 class="text-2xl font-bold">Registration closed</h1>
				<p class="mt-2 text-sm text-muted-foreground">
					Registration is currently closed. Please contact an administrator for access.
				</p>
			</div>
			<p class="text-center text-sm text-muted-foreground">
				Already have an account?
				<a href="/login" class="text-primary hover:underline">Sign in</a>
			</p>
		{:else if registered}
			<div class="text-center">
				<h1 class="text-2xl font-bold">Account created</h1>
				<p class="mt-2 text-sm text-muted-foreground">
					Your account is pending approval. You will be able to log in once an administrator activates it.
				</p>
			</div>
			<p class="text-center text-sm text-muted-foreground">
				<a href="/login" class="text-primary hover:underline">Back to login</a>
			</p>
		{:else}
			<div class="text-center">
				<h1 class="text-2xl font-bold">Create account</h1>
				<p class="text-sm text-muted-foreground">Join BoAT to start annotating</p>
			</div>

			{#if registrationMode === 'approval'}
				<div class="rounded-md bg-muted p-3 text-xs text-muted-foreground">
					Accounts require administrator approval before you can log in.
				</div>
			{/if}

			{#if error}
				<div id="register-error" class="rounded-md bg-destructive/10 p-3 text-sm text-destructive" role="alert">{error}</div>
			{/if}

			<form onsubmit={handleSubmit} class="space-y-4">
				<div class="grid grid-cols-2 gap-3">
					<div class="space-y-2">
						<label for="firstName" class="text-sm font-medium">First name</label>
						<Input id="firstName" bind:value={firstName} required aria-invalid={!!error} aria-describedby={error ? 'register-error' : undefined} />
					</div>
					<div class="space-y-2">
						<label for="lastName" class="text-sm font-medium">Last name</label>
						<Input id="lastName" bind:value={lastName} required aria-invalid={!!error} aria-describedby={error ? 'register-error' : undefined} />
					</div>
				</div>
				<div class="space-y-2">
					<label for="username" class="text-sm font-medium">Username</label>
					<Input id="username" bind:value={username} required aria-invalid={!!error} aria-describedby={error ? 'register-error' : undefined} />
				</div>
				<div class="space-y-2">
					<label for="email" class="text-sm font-medium">Email</label>
					<Input id="email" type="email" bind:value={email} required aria-invalid={!!error} aria-describedby={error ? 'register-error' : undefined} />
				</div>
				<div class="space-y-2">
					<label for="password" class="text-sm font-medium">Password</label>
					<Input id="password" type="password" bind:value={password} required aria-invalid={!!error} aria-describedby={error ? 'register-error' : undefined} />
				</div>
				<div class="space-y-2">
					<label for="password2" class="text-sm font-medium">Confirm password</label>
					<Input id="password2" type="password" bind:value={password2} required aria-invalid={!!error} aria-describedby={error ? 'register-error' : undefined} />
				</div>
				<Button type="submit" class="w-full" disabled={loading}>
					{loading ? 'Creating account...' : 'Register'}
				</Button>
			</form>

			<p class="text-center text-sm text-muted-foreground">
				Already have an account?
				<a href="/login" class="text-primary hover:underline">Sign in</a>
			</p>
		{/if}
	</div>
</div>
