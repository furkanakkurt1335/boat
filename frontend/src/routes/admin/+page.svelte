<script lang="ts">
	import { onMount } from 'svelte';
	import { api, ApiError } from '$api/client';
	import type { UserRead } from '$api/types';
	import { user } from '$stores/auth';
	import { toast } from '$stores/toast';
	import { goto } from '$app/navigation';
	import Button from '$components/common/Button.svelte';

	interface UserListResponse {
		users: UserRead[];
		total: number;
	}

	let users = $state<UserRead[]>([]);
	let showAll = $state(false);
	let loading = $state(true);

	let pendingUsers = $derived(users.filter((u) => !u.is_active));
	let activeUsers = $derived(users.filter((u) => u.is_active));

	onMount(async () => {
		if (!$user?.is_admin) {
			await goto('/dashboard');
			return;
		}
		await loadUsers();
	});

	async function loadUsers() {
		loading = true;
		try {
			const res = await api.get<UserListResponse>(
				`/admin/users${showAll ? '' : '?pending_only=true'}`
			);
			users = res.users;
		} catch (err) {
			toast.error(err instanceof ApiError ? err.detail : 'Failed to load users');
		} finally {
			loading = false;
		}
	}

	async function approveUser(userId: number) {
		try {
			await api.post<UserRead>('/admin/users/approve', { user_id: userId });
			toast.success('User approved');
			await loadUsers();
		} catch (err) {
			toast.error(err instanceof ApiError ? err.detail : 'Failed to approve user');
		}
	}

	async function rejectUser(userId: number) {
		try {
			await api.post<UserRead>('/admin/users/reject', { user_id: userId });
			toast.success('User deactivated');
			await loadUsers();
		} catch (err) {
			toast.error(err instanceof ApiError ? err.detail : 'Failed to deactivate user');
		}
	}
</script>

<div class="mx-auto max-w-5xl px-4 py-8">
	<h1 class="mb-6 text-2xl font-bold">User Management</h1>

	<div class="mb-4 flex items-center gap-4">
		<label class="flex items-center gap-2 text-sm">
			<input type="checkbox" bind:checked={showAll} onchange={loadUsers} class="rounded" />
			Show all users
		</label>
	</div>

	{#if loading}
		<p class="text-sm text-muted-foreground">Loading...</p>
	{:else}
		<!-- Pending users -->
		{#if pendingUsers.length > 0}
			<div class="mb-8">
				<h2 class="mb-3 text-lg font-semibold">
					Pending approval ({pendingUsers.length})
				</h2>
				<div class="overflow-x-auto rounded-lg border border-border">
					<table class="w-full text-sm">
						<thead class="border-b border-border bg-muted/50">
							<tr>
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">Username</th>
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">Name</th>
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">Email</th>
								<th class="px-3 py-2 text-right font-medium text-muted-foreground">Actions</th>
							</tr>
						</thead>
						<tbody>
							{#each pendingUsers as u}
								<tr class="border-b border-border/50 last:border-0">
									<td class="px-3 py-2 font-medium">{u.username}</td>
									<td class="px-3 py-2">{u.first_name} {u.last_name}</td>
									<td class="px-3 py-2 text-muted-foreground">{u.email}</td>
									<td class="px-3 py-2 text-right">
										<div class="flex justify-end gap-2">
											<Button size="sm" variant="primary" onclick={() => approveUser(u.id)}>
												Approve
											</Button>
											<Button size="sm" variant="destructive" onclick={() => rejectUser(u.id)}>
												Reject
											</Button>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{:else if !showAll}
			<p class="mb-8 text-sm text-muted-foreground">No pending users.</p>
		{/if}

		<!-- Active users (only when showAll) -->
		{#if showAll && activeUsers.length > 0}
			<div>
				<h2 class="mb-3 text-lg font-semibold">Active users ({activeUsers.length})</h2>
				<div class="overflow-x-auto rounded-lg border border-border">
					<table class="w-full text-sm">
						<thead class="border-b border-border bg-muted/50">
							<tr>
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">Username</th>
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">Name</th>
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">Email</th>
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">Role</th>
								<th class="px-3 py-2 text-right font-medium text-muted-foreground">Actions</th>
							</tr>
						</thead>
						<tbody>
							{#each activeUsers as u}
								<tr class="border-b border-border/50 last:border-0">
									<td class="px-3 py-2 font-medium">{u.username}</td>
									<td class="px-3 py-2">{u.first_name} {u.last_name}</td>
									<td class="px-3 py-2 text-muted-foreground">{u.email}</td>
									<td class="px-3 py-2">
										{#if u.is_admin}
											<span class="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">Admin</span>
										{:else}
											<span class="text-xs text-muted-foreground">User</span>
										{/if}
									</td>
									<td class="px-3 py-2 text-right">
										{#if !u.is_admin}
											<Button size="sm" variant="ghost" onclick={() => rejectUser(u.id)}>
												Deactivate
											</Button>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		{/if}
	{/if}
</div>
