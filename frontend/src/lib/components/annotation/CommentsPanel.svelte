<script lang="ts">
	import { onMount } from 'svelte';
	import { sentenceId } from '$stores/annotation';
	import { listComments, createComment, deleteComment } from '$api/comments';
	import { user } from '$stores/auth';
	import type { CommentRead } from '$api/types';
	import Button from '$components/common/Button.svelte';

	let comments = $state<CommentRead[]>([]);
	let newText = $state('');
	let loading = $state(true);

	onMount(async () => {
		await loadComments();
	});

	async function loadComments() {
		const sid = $sentenceId;
		if (!sid) return;
		loading = true;
		comments = await listComments(sid);
		loading = false;
	}

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		const sid = $sentenceId;
		if (!sid || !newText.trim()) return;
		await createComment(sid, newText.trim());
		newText = '';
		await loadComments();
	}

	async function handleDelete(commentId: number) {
		const sid = $sentenceId;
		if (!sid) return;
		await deleteComment(sid, commentId);
		await loadComments();
	}

	function formatDate(iso: string) {
		return new Date(iso).toLocaleString();
	}
</script>

<div class="flex h-full flex-col">
	<div class="border-b border-border px-4 py-3">
		<h3 class="text-sm font-semibold">Discussion</h3>
	</div>

	<div class="flex-1 overflow-auto p-3 space-y-3">
		{#if loading}
			<p class="text-xs text-muted-foreground">Loading...</p>
		{:else if comments.length === 0}
			<p class="text-xs text-muted-foreground">No comments yet.</p>
		{:else}
			{#each comments as comment}
				<div class="rounded-md border border-border p-3">
					<div class="flex items-center justify-between mb-1">
						<span class="text-xs font-medium">{comment.username}</span>
						<div class="flex items-center gap-2">
							<span class="text-xs text-muted-foreground">{formatDate(comment.created_at)}</span>
							{#if comment.user_id === $user?.id}
								<button
									onclick={() => handleDelete(comment.id)}
									class="text-xs text-destructive hover:text-destructive/80 cursor-pointer"
								>
									&times;
								</button>
							{/if}
						</div>
					</div>
					<p class="text-sm">{comment.text}</p>
				</div>
			{/each}
		{/if}
	</div>

	<form onsubmit={handleSubmit} class="border-t border-border p-3">
		<div class="flex gap-2">
			<textarea
				bind:value={newText}
				rows="2"
				placeholder="Add a comment..."
				class="flex-1 rounded-md border border-input bg-background px-3 py-2 text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
			></textarea>
			<Button size="sm" type="submit" disabled={!newText.trim()}>Post</Button>
		</div>
	</form>
</div>
