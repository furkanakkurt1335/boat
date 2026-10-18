<script lang="ts">
	import { onMount } from 'svelte';
	import { user } from '$stores/auth';
	import { listTreebanks } from '$api/treebanks';
	import { getMyAnnotations } from '$api/annotations';
	import { AnnotationStatus } from '$api/types';
	import type { TreebankWithProgress, AnnotationDetail } from '$api/types';
	import StatusBadge from '$components/common/StatusBadge.svelte';
	import Skeleton from '$components/common/Skeleton.svelte';
	import { FolderTree, FileText, PenLine, CheckCircle2 } from 'lucide-svelte';

	let treebanks = $state<TreebankWithProgress[]>([]);
	let allAnnotations = $state<AnnotationDetail[]>([]);
	let recentAnnotations = $state<AnnotationDetail[]>([]);
	let loading = $state(true);

	let totalAnnotations = $state(0);
	let completedCount = $state(0);
	let lastDraft = $state<AnnotationDetail | null>(null);

	onMount(async () => {
		const [tb, ann] = await Promise.all([listTreebanks(), getMyAnnotations()]);
		treebanks = tb;
		allAnnotations = ann;
		totalAnnotations = ann.length;
		completedCount = ann.filter((a) => a.status === AnnotationStatus.SUBMITTED || a.status === AnnotationStatus.APPROVED).length;
		lastDraft = ann.find((a) => a.status === AnnotationStatus.DRAFT) ?? null;
		recentAnnotations = ann.slice(0, 5);
		loading = false;
	});

	function totalSentences() {
		return treebanks.reduce((s, t) => s + t.sentence_count, 0);
	}
</script>

<div class="mx-auto max-w-7xl px-4 py-8">
	<h1 class="mb-6 text-2xl font-bold">Welcome, {$user?.first_name || $user?.username}</h1>

	{#if loading}
		<div class="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
			{#each Array(4) as _}
				<div class="rounded-lg border border-border p-5">
					<Skeleton class="mb-2 h-4 w-24" />
					<Skeleton class="h-8 w-16" />
				</div>
			{/each}
		</div>
		<Skeleton class="mb-3 h-6 w-32" />
		<div class="space-y-2">
			{#each Array(3) as _}
				<Skeleton class="h-12 w-full rounded-lg" />
			{/each}
		</div>
	{:else}
		<div class="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
			<div class="rounded-lg border border-border p-5">
				<div class="flex items-center gap-2 text-sm text-muted-foreground">
					<FolderTree class="h-4 w-4" />
					<span>Treebanks</span>
				</div>
				<p class="mt-1 text-3xl font-bold">{treebanks.length}</p>
			</div>
			<div class="rounded-lg border border-border p-5">
				<div class="flex items-center gap-2 text-sm text-muted-foreground">
					<FileText class="h-4 w-4" />
					<span>Total sentences</span>
				</div>
				<p class="mt-1 text-3xl font-bold">{totalSentences()}</p>
			</div>
			<div class="rounded-lg border border-border p-5">
				<div class="flex items-center gap-2 text-sm text-muted-foreground">
					<PenLine class="h-4 w-4" />
					<span>My annotations</span>
				</div>
				<p class="mt-1 text-3xl font-bold">{totalAnnotations}</p>
			</div>
			<div class="rounded-lg border border-border p-5">
				<div class="flex items-center gap-2 text-sm text-muted-foreground">
					<CheckCircle2 class="h-4 w-4" />
					<span>Completed</span>
				</div>
				<p class="mt-1 text-3xl font-bold">{completedCount}</p>
			</div>
		</div>

		{#if lastDraft}
			<section class="mb-8">
				<h2 class="mb-3 text-lg font-semibold">Continue where you left off</h2>
				<a
					href="/annotate/{lastDraft.treebank_title}/{lastDraft.sentence_order}"
					class="flex items-center justify-between rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 transition-colors hover:bg-primary/10"
				>
					<div>
						<p class="text-sm font-medium">{lastDraft.sentence_sent_id}</p>
						<p class="text-xs text-muted-foreground max-w-md truncate">{lastDraft.sentence_text}</p>
					</div>
					<div class="flex items-center gap-2">
						<StatusBadge status={lastDraft.status} />
						<span class="text-xs text-muted-foreground">{lastDraft.treebank_title}</span>
						<span class="text-sm text-primary font-medium">Continue &rarr;</span>
					</div>
				</a>
			</section>
		{/if}

		{#if treebanks.length > 0}
			<section class="mb-8">
				<h2 class="mb-3 text-lg font-semibold">Treebanks</h2>
				<div class="overflow-hidden rounded-lg border border-border">
					<table class="w-full text-sm">
						<thead class="bg-muted text-left">
							<tr>
								<th class="px-4 py-2 font-medium">Title</th>
								<th class="px-4 py-2 font-medium">Language</th>
								<th class="px-4 py-2 font-medium">Sentences</th>
								<th class="px-4 py-2 font-medium">Progress</th>
							</tr>
						</thead>
						<tbody>
							{#each treebanks as tb}
								{@const pct = tb.sentence_count > 0 ? Math.round((tb.complete_count / tb.sentence_count) * 100) : 0}
								<tr class="border-t border-border hover:bg-muted/50">
									<td class="px-4 py-2">
										<a href="/treebanks/{tb.title}" class="text-primary hover:underline">{tb.title}</a>
									</td>
									<td class="px-4 py-2 text-muted-foreground">{tb.language}</td>
									<td class="px-4 py-2">{tb.sentence_count}</td>
									<td class="px-4 py-2">
										<div class="flex items-center gap-2">
											<div class="h-2 w-24 overflow-hidden rounded-full bg-muted">
												<div class="h-full bg-primary transition-all" style="width: {pct}%"></div>
											</div>
											<span class="text-xs text-muted-foreground">{pct}%</span>
										</div>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		{/if}

		{#if recentAnnotations.length > 0}
			<section>
				<h2 class="mb-3 text-lg font-semibold">Recent annotations</h2>
				<div class="space-y-2">
					{#each recentAnnotations as ann}
						<div class="flex items-center justify-between rounded-lg border border-border px-4 py-3">
							<div>
								<span class="text-sm font-medium">{ann.sentence_sent_id ?? `#${ann.sentence_id}`}</span>
								<span class="ml-2 text-xs text-muted-foreground">{ann.treebank_title}</span>
								<StatusBadge status={ann.status} />
							</div>
							<a href="/annotate/{ann.treebank_title}/{ann.sentence_order}" class="text-sm text-primary hover:underline">Edit</a>
						</div>
					{/each}
				</div>
			</section>
		{/if}
	{/if}
</div>
