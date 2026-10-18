<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { getTreebankByTitle, uploadConllu, exportConllu, getTreebankStats } from '$api/treebanks';
	import { listSentences, createSentence, deleteSentence } from '$api/sentences';
	import { ApiError } from '$api/client';
	import type { TreebankRead, SentenceBrief, TreebankStats } from '$api/types';
	import Button from '$components/common/Button.svelte';
	import Input from '$components/common/Input.svelte';
	import Modal from '$components/common/Modal.svelte';
	import Breadcrumb from '$components/layout/Breadcrumb.svelte';
	import EmptyState from '$components/common/EmptyState.svelte';
	import ErrorState from '$components/common/ErrorState.svelte';
	import Skeleton from '$components/common/Skeleton.svelte';
	import { FileText } from 'lucide-svelte';

	const treebankTitle = $derived(decodeURIComponent(page.params.title!));

	let treebank = $state<TreebankRead | null>(null);
	let sentences = $state<SentenceBrief[]>([]);
	let loading = $state(true);
	let error = $state('');
	let currentPage = $state(0);
	const pageSize = 20;
	let allSentences = $state<SentenceBrief[]>([]);

	// Tabs
	let activeTab = $state<'sentences' | 'statistics'>('sentences');

	// Statistics
	let stats = $state<TreebankStats | null>(null);
	let statsLoading = $state(false);
	let statsError = $state('');
	let statsLoaded = $state(false);

	async function loadStats() {
		if (!treebank || statsLoaded) return;
		statsLoading = true;
		statsError = '';
		try {
			stats = await getTreebankStats(treebank.id);
			statsLoaded = true;
		} catch (err) {
			statsError = err instanceof ApiError ? err.detail : 'Failed to load statistics';
		} finally {
			statsLoading = false;
		}
	}

	function switchTab(tab: 'sentences' | 'statistics') {
		activeTab = tab;
		if (tab === 'statistics') loadStats();
	}

	function computeSentenceStats(lengths: number[]) {
		if (lengths.length === 0) return { min: 0, max: 0, mean: 0, median: 0 };
		const sorted = [...lengths].sort((a, b) => a - b);
		const min = sorted[0];
		const max = sorted[sorted.length - 1];
		const mean = sorted.reduce((a, b) => a + b, 0) / sorted.length;
		const mid = Math.floor(sorted.length / 2);
		const median = sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
		return { min, max, mean: Math.round(mean * 10) / 10, median };
	}

	// Filtering
	let activeFilters = $state<Record<string, string>>({});
	let showFilters = $state(false);

	// Auto-detect filterable metadata keys (keys with <= 20 distinct values)
	const filterableKeys = $derived(() => {
		const keyCounts = new Map<string, Map<string, number>>();
		for (const sent of allSentences) {
			if (!sent.metadata) continue;
			for (const [key, val] of Object.entries(sent.metadata)) {
				if (!keyCounts.has(key)) keyCounts.set(key, new Map());
				const valMap = keyCounts.get(key)!;
				valMap.set(val, (valMap.get(val) ?? 0) + 1);
			}
		}
		const result: { key: string; values: { value: string; count: number }[] }[] = [];
		for (const [key, valMap] of keyCounts) {
			if (valMap.size >= 2 && valMap.size <= 20) {
				const values = [...valMap.entries()]
					.map(([value, count]) => ({ value, count }))
					.sort((a, b) => b.count - a.count);
				result.push({ key, values });
			}
		}
		return result.sort((a, b) => a.key.localeCompare(b.key));
	});

	const filteredSentences = $derived(() => {
		const keys = Object.entries(activeFilters).filter(([, v]) => v !== '');
		if (keys.length === 0) return allSentences;
		return allSentences.filter((sent) => {
			if (!sent.metadata) return false;
			return keys.every(([key, val]) => sent.metadata?.[key] === val);
		});
	});

	const paginatedSentences = $derived(
		filteredSentences().slice(currentPage * pageSize, (currentPage + 1) * pageSize)
	);

	const hasActiveFilters = $derived(Object.values(activeFilters).some((v) => v !== ''));

	function clearFilters() {
		activeFilters = {};
		currentPage = 0;
	}

	function setFilter(key: string, value: string) {
		activeFilters = { ...activeFilters, [key]: value };
		currentPage = 0;
	}

	// Add sentence
	let showAdd = $state(false);
	let newSentId = $state('');
	let newText = $state('');
	let addError = $state('');

	// Upload
	let showUpload = $state(false);
	let uploadFile = $state<File | null>(null);
	let uploadMsg = $state('');
	let uploadError = $state('');

	// Delete
	let showDelete = $state(false);
	let deleteTarget = $state<SentenceBrief | null>(null);

	onMount(loadData);

	async function loadData() {
		loading = true;
		error = '';
		try {
			const tb = await getTreebankByTitle(treebankTitle);
			treebank = tb;
			allSentences = await listSentences(tb.id);
		} catch (err) {
			error = err instanceof ApiError ? err.detail : 'Failed to load treebank';
		} finally {
			loading = false;
		}
	}

	function goPage(p: number) {
		currentPage = p;
	}

	async function handleAddSentence(e: SubmitEvent) {
		e.preventDefault();
		addError = '';
		if (!treebank) return;
		try {
			await createSentence(treebank.id, newSentId, newText);
			showAdd = false;
			newSentId = '';
			newText = '';
			await loadData();
		} catch (err) {
			addError = err instanceof ApiError ? err.detail : 'Failed to add sentence';
		}
	}

	async function handleUpload(e: SubmitEvent) {
		e.preventDefault();
		uploadError = '';
		uploadMsg = '';
		if (!uploadFile || !treebank) return;
		try {
			const result = await uploadConllu(treebank.id, uploadFile);
			uploadMsg = `Imported ${result.sentences_created} sentences.`;
			uploadFile = null;
			await loadData();
		} catch (err) {
			uploadError = err instanceof ApiError ? err.detail : 'Upload failed';
		}
	}

	async function handleDelete() {
		if (!deleteTarget) return;
		await deleteSentence(deleteTarget.id);
		deleteTarget = null;
		showDelete = false;
		await loadData();
	}

	function annotate(sentence: SentenceBrief) {
		window.location.href = `/annotate/${treebankTitle}/${sentence.order}`;
	}

	function onFileChange(e: Event) {
		const input = e.target as HTMLInputElement;
		uploadFile = input.files?.[0] ?? null;
	}
</script>

<div class="mx-auto max-w-7xl px-4 py-8">
	{#if loading}
		<div class="mb-6">
			<Skeleton class="mb-2 h-4 w-48" />
			<Skeleton class="mb-1 h-8 w-64" />
			<Skeleton class="h-4 w-24" />
		</div>
		<div class="overflow-hidden rounded-lg border border-border">
			{#each Array(5) as _}
				<div class="flex items-center gap-4 border-t border-border px-4 py-3">
					<Skeleton class="h-4 w-8" />
					<Skeleton class="h-4 w-24" />
					<Skeleton class="h-4 w-full max-w-sm" />
				</div>
			{/each}
		</div>
	{:else if error}
		<ErrorState message={error} onRetry={loadData} />
	{:else if treebank}
		<div class="mb-6">
			<div class="mb-2">
				<Breadcrumb crumbs={[{ label: 'Treebanks', href: '/treebanks' }, { label: treebank.title }]} />
			</div>
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-2xl font-bold">{treebank.title}</h1>
					<div class="mt-1 flex items-center gap-3 text-sm text-muted-foreground">
						<span>{treebank.language}</span>
						<span class="text-border">|</span>
						<span>{allSentences.length} sentences</span>
						{#if treebank.created_at}
							<span class="text-border">|</span>
							<span>Created {new Date(treebank.created_at).toLocaleDateString()}</span>
						{/if}
					</div>
				</div>
				<div class="flex gap-2">
					<a
						href="/treebanks/{treebankTitle}/agreement"
						class="inline-flex h-9 items-center rounded-md border border-input bg-background px-4 text-sm font-medium hover:bg-accent hover:text-accent-foreground"
					>Agreement</a>
					<Button variant="outline" onclick={() => (showUpload = true)}>Upload CoNLL-U</Button>
					<Button variant="outline" onclick={() => (showAdd = true)}>Add sentence</Button>
					<Button variant="outline" onclick={() => exportConllu(treebank!.id)}>Export</Button>
				</div>
			</div>
		</div>

		<!-- Tabs -->
		<div class="mb-6 flex gap-1 border-b border-border">
			<button
				onclick={() => switchTab('sentences')}
				class="cursor-pointer px-4 py-2 text-sm font-medium transition-colors {activeTab === 'sentences' ? 'border-b-2 border-primary text-foreground' : 'text-muted-foreground hover:text-foreground'}"
			>
				Sentences
			</button>
			<button
				onclick={() => switchTab('statistics')}
				class="cursor-pointer px-4 py-2 text-sm font-medium transition-colors {activeTab === 'statistics' ? 'border-b-2 border-primary text-foreground' : 'text-muted-foreground hover:text-foreground'}"
			>
				Statistics
			</button>
		</div>

		{#if activeTab === 'statistics'}
			{#if statsLoading}
				<div class="space-y-4">
					<Skeleton class="h-6 w-48" />
					<Skeleton class="h-40 w-full" />
					<Skeleton class="h-6 w-48" />
					<Skeleton class="h-40 w-full" />
				</div>
			{:else if statsError}
				<ErrorState message={statsError} onRetry={loadStats} />
			{:else if stats}
				{@const sentStats = computeSentenceStats(stats.sentence_lengths)}
				<!-- Summary cards -->
				<div class="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
					<div class="rounded-lg border border-border p-4">
						<div class="text-sm text-muted-foreground">Total sentences</div>
						<div class="text-2xl font-bold">{stats.total_sentences.toLocaleString()}</div>
					</div>
					<div class="rounded-lg border border-border p-4">
						<div class="text-sm text-muted-foreground">Total tokens</div>
						<div class="text-2xl font-bold">{stats.total_tokens.toLocaleString()}</div>
					</div>
					<div class="rounded-lg border border-border p-4">
						<div class="text-sm text-muted-foreground">Mean sentence length</div>
						<div class="text-2xl font-bold">{sentStats.mean}</div>
					</div>
					<div class="rounded-lg border border-border p-4">
						<div class="text-sm text-muted-foreground">Median sentence length</div>
						<div class="text-2xl font-bold">{sentStats.median}</div>
					</div>
				</div>

				<!-- UPOS distribution -->
				{#if Object.keys(stats.upos_distribution).length > 0}
					{@const uposMax = Math.max(...Object.values(stats.upos_distribution))}
					<div class="mb-8">
						<h2 class="mb-3 text-lg font-semibold">UPOS distribution</h2>
						<div class="space-y-1.5">
							{#each Object.entries(stats.upos_distribution) as [tag, count]}
								<div class="flex items-center gap-3 text-sm">
									<span class="w-16 shrink-0 text-right font-mono text-xs">{tag}</span>
									<div class="h-5 flex-1 rounded bg-muted">
										<div
											class="h-full rounded bg-primary/70"
											style="width: {(count / uposMax) * 100}%"
										></div>
									</div>
									<span class="w-16 shrink-0 text-right text-muted-foreground tabular-nums">{count.toLocaleString()}</span>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- DEPREL distribution -->
				{#if Object.keys(stats.deprel_distribution).length > 0}
					{@const deprelMax = Math.max(...Object.values(stats.deprel_distribution))}
					<div class="mb-8">
						<h2 class="mb-3 text-lg font-semibold">DEPREL distribution</h2>
						<div class="space-y-1.5">
							{#each Object.entries(stats.deprel_distribution) as [rel, count]}
								<div class="flex items-center gap-3 text-sm">
									<span class="w-24 shrink-0 text-right font-mono text-xs">{rel}</span>
									<div class="h-5 flex-1 rounded bg-muted">
										<div
											class="h-full rounded bg-blue-500/70 dark:bg-blue-400/70"
											style="width: {(count / deprelMax) * 100}%"
										></div>
									</div>
									<span class="w-16 shrink-0 text-right text-muted-foreground tabular-nums">{count.toLocaleString()}</span>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Top lemmas -->
				{#if stats.top_lemmas.length > 0}
					<div class="mb-8">
						<h2 class="mb-3 text-lg font-semibold">Top 20 lemmas</h2>
						<div class="overflow-hidden rounded-lg border border-border">
							<table class="w-full text-sm">
								<thead class="bg-muted text-left">
									<tr>
										<th class="px-4 py-2 font-medium w-12">#</th>
										<th class="px-4 py-2 font-medium">Lemma</th>
										<th class="px-4 py-2 font-medium text-right">Count</th>
									</tr>
								</thead>
								<tbody>
									{#each stats.top_lemmas as { lemma, count }, i}
										<tr class="border-t border-border">
											<td class="px-4 py-2 text-muted-foreground">{i + 1}</td>
											<td class="px-4 py-2 font-mono">{lemma}</td>
											<td class="px-4 py-2 text-right tabular-nums">{count.toLocaleString()}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{/if}

				<!-- Sentence length stats -->
				<div class="mb-8">
					<h2 class="mb-3 text-lg font-semibold">Sentence length</h2>
					<div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
						<div class="rounded-lg border border-border p-4">
							<div class="text-sm text-muted-foreground">Min</div>
							<div class="text-xl font-bold">{sentStats.min}</div>
						</div>
						<div class="rounded-lg border border-border p-4">
							<div class="text-sm text-muted-foreground">Max</div>
							<div class="text-xl font-bold">{sentStats.max}</div>
						</div>
						<div class="rounded-lg border border-border p-4">
							<div class="text-sm text-muted-foreground">Mean</div>
							<div class="text-xl font-bold">{sentStats.mean}</div>
						</div>
						<div class="rounded-lg border border-border p-4">
							<div class="text-sm text-muted-foreground">Median</div>
							<div class="text-xl font-bold">{sentStats.median}</div>
						</div>
					</div>
				</div>
			{/if}
		{:else if allSentences.length === 0}
			<EmptyState icon={FileText} title="No sentences yet" description="Upload a CoNLL-U file or add sentences manually.">
				<div class="flex gap-2">
					<Button variant="outline" size="sm" onclick={() => (showUpload = true)}>Upload CoNLL-U</Button>
					<Button variant="outline" size="sm" onclick={() => (showAdd = true)}>Add sentence</Button>
				</div>
			</EmptyState>
		{:else}
			<!-- Filter bar -->
			{#if filterableKeys().length > 0}
				<div class="mb-4 flex flex-wrap items-center gap-3">
					{#each filterableKeys() as { key, values }}
						<div class="flex items-center gap-1.5">
							<label for="filter-{key}" class="text-xs font-medium text-muted-foreground">{key}</label>
							<select
								id="filter-{key}"
								value={activeFilters[key] ?? ''}
								onchange={(e) => setFilter(key, (e.target as HTMLSelectElement).value)}
								class="h-7 rounded border border-input bg-background px-2 text-xs focus-visible:ring-2 focus-visible:ring-ring {activeFilters[key] ? 'text-foreground font-medium' : 'text-muted-foreground'}"
							>
								<option value="">All</option>
								{#each values as { value, count }}
									<option value={value}>{value} ({count})</option>
								{/each}
							</select>
						</div>
					{/each}
					{#if hasActiveFilters}
						<button onclick={clearFilters} class="text-xs text-muted-foreground hover:text-foreground cursor-pointer underline">
							Clear filters
						</button>
						<span class="text-xs text-muted-foreground">
							{filteredSentences().length} of {allSentences.length} sentences
						</span>
					{/if}
				</div>
			{/if}

			<div class="overflow-hidden rounded-lg border border-border">
				<table class="w-full text-sm">
					<thead class="bg-muted text-left">
						<tr>
							<th class="px-4 py-3 font-medium w-16">#</th>
							<th class="px-4 py-3 font-medium w-32">Sent ID</th>
							<th class="px-4 py-3 font-medium">Text</th>
							<th class="px-4 py-3 font-medium w-36">Actions</th>
						</tr>
					</thead>
					<tbody>
						{#each paginatedSentences as sent}
							<tr class="border-t border-border hover:bg-muted/50">
								<td class="px-4 py-3 text-muted-foreground">{sent.order}</td>
								<td class="px-4 py-3 font-mono text-xs">{sent.sent_id}</td>
								<td class="px-4 py-3 max-w-xl truncate">{sent.text}</td>
								<td class="px-4 py-3">
									<div class="flex gap-2">
										<button
											onclick={() => annotate(sent)}
											class="text-xs text-primary hover:underline cursor-pointer"
										>
											Annotate
										</button>
										<button
											onclick={() => { deleteTarget = sent; showDelete = true; }}
											class="text-xs text-destructive hover:text-destructive/80 cursor-pointer"
										>
											Delete
										</button>
									</div>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Pagination -->
			<div class="mt-4 flex items-center justify-between">
				<Button variant="outline" size="sm" disabled={currentPage === 0} onclick={() => goPage(currentPage - 1)}>
					Previous
				</Button>
				<span class="text-sm text-muted-foreground">Page {currentPage + 1}</span>
				<Button
					variant="outline"
					size="sm"
					disabled={(currentPage + 1) * pageSize >= filteredSentences().length}
					onclick={() => goPage(currentPage + 1)}
				>
					Next
				</Button>
			</div>
		{/if}
	{/if}
</div>

<!-- Add sentence modal -->
<Modal open={showAdd} title="Add sentence" onclose={() => (showAdd = false)}>
	{#if addError}
		<div class="mb-3 rounded-md bg-destructive/10 p-3 text-sm text-destructive">{addError}</div>
	{/if}
	<form onsubmit={handleAddSentence} class="space-y-4">
		<div class="space-y-2">
			<label for="sent-id" class="text-sm font-medium">Sentence ID</label>
			<Input id="sent-id" bind:value={newSentId} required placeholder="e.g. sent-001" />
		</div>
		<div class="space-y-2">
			<label for="sent-text" class="text-sm font-medium">Text</label>
			<textarea
				id="sent-text"
				bind:value={newText}
				required
				rows="3"
				class="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
				placeholder="Enter sentence text..."
			></textarea>
		</div>
		<div class="flex justify-end gap-2">
			<Button variant="ghost" onclick={() => (showAdd = false)}>Cancel</Button>
			<Button type="submit">Add</Button>
		</div>
	</form>
</Modal>

<!-- Upload modal -->
<Modal open={showUpload} title="Upload CoNLL-U file" onclose={() => { showUpload = false; uploadMsg = ''; uploadError = ''; }}>
	{#if uploadError}
		<div class="mb-3 rounded-md bg-destructive/10 p-3 text-sm text-destructive">{uploadError}</div>
	{/if}
	{#if uploadMsg}
		<div class="mb-3 rounded-md bg-success/10 p-3 text-sm text-success">{uploadMsg}</div>
	{/if}
	<form onsubmit={handleUpload} class="space-y-4">
		<div class="space-y-2">
			<label for="conllu-file" class="text-sm font-medium">CoNLL-U file</label>
			<input
				id="conllu-file"
				type="file"
				accept=".conllu,.conll,.txt"
				onchange={onFileChange}
				class="block w-full text-sm file:mr-4 file:rounded-md file:border-0 file:bg-primary file:px-4 file:py-2 file:text-sm file:font-medium file:text-primary-foreground hover:file:bg-primary/90"
			/>
		</div>
		<div class="flex justify-end gap-2">
			<Button variant="ghost" onclick={() => { showUpload = false; uploadMsg = ''; uploadError = ''; }}>Close</Button>
			<Button type="submit" disabled={!uploadFile}>Upload</Button>
		</div>
	</form>
</Modal>

<!-- Delete confirmation -->
<Modal open={showDelete} title="Delete sentence" onclose={() => (showDelete = false)}>
	<p class="text-sm">
		Are you sure you want to delete sentence <strong>{deleteTarget?.sent_id}</strong>? All annotations will be removed.
	</p>
	{#snippet actions()}
		<Button variant="ghost" onclick={() => (showDelete = false)}>Cancel</Button>
		<Button variant="destructive" onclick={handleDelete}>Delete</Button>
	{/snippet}
</Modal>
