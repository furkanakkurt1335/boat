<script lang="ts">
	import { onMount } from 'svelte';
	import { getMyAnnotations } from '$api/annotations';
	import type { AnnotationDetail } from '$api/types';
	import Button from '$components/common/Button.svelte';
	import StatusBadge from '$components/common/StatusBadge.svelte';
	import EmptyState from '$components/common/EmptyState.svelte';
	import Skeleton from '$components/common/Skeleton.svelte';
	import { PenLine } from 'lucide-svelte';

	const statusFilters = [
		{ label: 'All', value: undefined },
		{ label: 'Untouched', value: 0 },
		{ label: 'Edited', value: 2 },
	] as const;

	let annotations = $state<AnnotationDetail[]>([]);
	let loading = $state(true);
	let filterStatus = $state<number | undefined>(undefined);

	onMount(loadAnnotations);

	async function loadAnnotations() {
		loading = true;
		annotations = await getMyAnnotations(filterStatus);
		loading = false;
	}

	async function setFilter(status: number | undefined) {
		filterStatus = status;
		await loadAnnotations();
	}
</script>

<div class="mx-auto max-w-7xl px-4 py-8">
	<h1 class="mb-6 text-2xl font-bold">My Annotations</h1>

	<!-- Status filter -->
	<div class="mb-4 flex gap-2">
		{#each statusFilters as { label, value }}
			<button
				onclick={() => setFilter(value)}
				class="rounded-full px-3 py-1 text-xs font-medium transition-colors cursor-pointer
					{filterStatus === value ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'}"
			>
				{label}
			</button>
		{/each}
	</div>

	{#if loading}
		<div class="space-y-2">
			{#each Array(5) as _}
				<div class="flex items-center justify-between rounded-lg border border-border px-4 py-3">
					<div class="flex items-center gap-3">
						<Skeleton class="h-5 w-16 rounded-full" />
						<div>
							<Skeleton class="mb-1 h-4 w-32" />
							<Skeleton class="h-3 w-48" />
						</div>
					</div>
					<Skeleton class="h-4 w-16" />
				</div>
			{/each}
		</div>
	{:else if annotations.length === 0}
		<EmptyState icon={PenLine} title="No annotations yet" description="Start annotating sentences from a treebank.">
			<a href="/treebanks" class="text-sm text-primary hover:underline">Browse treebanks</a>
		</EmptyState>
	{:else}
		<div class="space-y-2">
			{#each annotations as ann}
				<div class="flex items-center justify-between rounded-lg border border-border px-4 py-3 hover:bg-muted/50">
					<div class="flex items-center gap-3">
						<StatusBadge status={ann.status} />
						<div>
							<p class="text-sm font-medium">{ann.sentence_sent_id}</p>
							<p class="text-xs text-muted-foreground max-w-lg truncate">{ann.sentence_text}</p>
						</div>
					</div>
					<div class="flex items-center gap-3">
						<span class="text-xs text-muted-foreground">{ann.treebank_title}</span>
						<a
							href="/annotate/{ann.treebank_title}/{ann.sentence_order}"
							class="text-sm text-primary hover:underline"
						>
							Edit
						</a>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
