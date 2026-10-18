<script lang="ts">
	import { onMount } from 'svelte';
	import { search, searchStructural, type SearchQuery } from '$api/search';
	import { listTreebanks } from '$api/treebanks';
	import type {
		SearchResult,
		SearchResponse,
		TreebankWithProgress,
		StructuralQuery,
		StructuralMatch,
		StructuralSearchResponse
	} from '$api/types';
	import Button from '$components/common/Button.svelte';
	import Input from '$components/common/Input.svelte';
	import SearchAutocomplete from '$components/common/SearchAutocomplete.svelte';
	import StructuralQueryBuilder from '$components/search/StructuralQueryBuilder.svelte';
	import { UPOS_TAGS, DEPREL_TAGS, FEATURES, DEFAULT_MISC } from '$utils/ud-tagsets';

	const FLAT_FIELD_OPTIONS = [
		'sent_id', 'text', 'form', 'lemma', 'upos', 'xpos', 'feats', 'misc'
	];

	const FEATURE_KEYS = Object.keys(FEATURES);
	const MISC_KEYS = Object.keys(DEFAULT_MISC);

	interface QueryRow {
		field: string;
		value: string;
		featKey: string;
		featValue: string;
		miscKey: string;
		miscValue: string;
	}

	function makeRow(field = 'upos'): QueryRow {
		return { field, value: '', featKey: '', featValue: '', miscKey: '', miscValue: '' };
	}

	// --- Search mode ---
	let searchMode = $state<'flat' | 'structural'>('flat');

	// --- Common state ---
	let treebanks = $state<TreebankWithProgress[]>([]);
	let loading = $state(false);
	let searched = $state(false);

	// --- Flat search state ---
	let selectedTreebank = $state('');
	let queries = $state<QueryRow[]>([makeRow('upos')]);
	let flatResults = $state<SearchResult[]>([]);
	let flatTotal = $state(0);
	let flatPage = $state(0);
	const pageSize = 20;

	// --- Structural search state ---
	let structuralResults = $state<StructuralMatch[]>([]);
	let structuralTotal = $state(0);
	let structuralPage = $state(0);
	let lastStructuralQuery = $state<StructuralQuery | null>(null);

	onMount(async () => {
		treebanks = await listTreebanks();
	});

	// --- Flat search handlers ---
	function addRow() {
		queries = [...queries, makeRow('form')];
	}

	function removeRow(index: number) {
		queries = queries.filter((_, i) => i !== index);
	}

	function resolveValue(q: QueryRow): string {
		if (q.field === 'feats') {
			if (q.featKey && q.featValue) return `${q.featKey}=${q.featValue}`;
			if (q.featKey) return q.featKey;
			return '';
		}
		if (q.field === 'misc') {
			if (q.miscKey && q.miscValue) return `${q.miscKey}=${q.miscValue}`;
			if (q.miscKey) return q.miscKey;
			return '';
		}
		return q.value;
	}

	function buildActiveQueries(): SearchQuery[] {
		return queries
			.map((q) => ({ field: q.field, value: resolveValue(q).trim() }))
			.filter((q) => q.value);
	}

	async function handleFlatSearch(e?: SubmitEvent) {
		e?.preventDefault();
		loading = true;
		flatPage = 0;
		const activeQueries = buildActiveQueries();
		const response = await search(activeQueries, selectedTreebank || undefined, 0, pageSize);
		flatResults = response.results;
		flatTotal = response.total;
		searched = true;
		loading = false;
	}

	async function goFlatPage(p: number) {
		flatPage = p;
		loading = true;
		const activeQueries = buildActiveQueries();
		const response = await search(activeQueries, selectedTreebank || undefined, p * pageSize, pageSize);
		flatResults = response.results;
		flatTotal = response.total;
		loading = false;
	}

	function handleFieldChange(index: number, newField: string) {
		queries[index].field = newField;
		queries[index].value = '';
		queries[index].featKey = '';
		queries[index].featValue = '';
		queries[index].miscKey = '';
		queries[index].miscValue = '';
	}

	function getMiscValueOptions(key: string): string[] | null {
		return DEFAULT_MISC[key] ?? null;
	}

	// --- Structural search handlers ---
	async function handleStructuralSearch(query: StructuralQuery) {
		loading = true;
		structuralPage = 0;
		lastStructuralQuery = { ...query, limit: pageSize, offset: 0 };
		const response = await searchStructural(lastStructuralQuery);
		structuralResults = response.results;
		structuralTotal = response.total;
		searched = true;
		loading = false;
	}

	async function goStructuralPage(p: number) {
		if (!lastStructuralQuery) return;
		structuralPage = p;
		loading = true;
		const query = { ...lastStructuralQuery, offset: p * pageSize, limit: pageSize };
		const response = await searchStructural(query);
		structuralResults = response.results;
		structuralTotal = response.total;
		loading = false;
	}

	// --- Mode switching ---
	function switchMode(mode: 'flat' | 'structural') {
		searchMode = mode;
		searched = false;
	}

	/**
	 * Highlight matched token IDs in a sentence text.
	 * matched_token_ids are CoNLL-U ID strings (1-based). We split by whitespace
	 * and highlight the corresponding indices. Returns an array of { text, highlighted } segments.
	 */
	function highlightTokens(text: string, matchedIds: string[]): { text: string; highlighted: boolean }[] {
		const words = text.split(/\s+/);
		// Parse integer IDs (skip multiword tokens like "1-2")
		const matchedIndices = new Set(
			matchedIds
				.map((id) => parseInt(id, 10))
				.filter((n) => !isNaN(n))
		);

		const segments: { text: string; highlighted: boolean }[] = [];
		let currentHighlighted = false;
		let currentText = '';

		for (let i = 0; i < words.length; i++) {
			const wordIdx = i + 1; // CoNLL-U is 1-based
			const isMatch = matchedIndices.has(wordIdx);

			if (isMatch !== currentHighlighted && currentText) {
				segments.push({ text: currentText, highlighted: currentHighlighted });
				currentText = '';
			}
			currentHighlighted = isMatch;
			currentText += (currentText ? ' ' : '') + words[i];
		}
		if (currentText) {
			segments.push({ text: currentText, highlighted: currentHighlighted });
		}

		return segments;
	}
</script>

<div class="mx-auto max-w-7xl px-4 py-8">
	<h1 class="mb-6 text-2xl font-bold">Search</h1>

	<!-- Mode toggle -->
	<div class="mb-6 flex gap-1 rounded-lg border border-border bg-muted p-1 w-fit">
		<button
			class="rounded-md px-4 py-1.5 text-sm font-medium transition-colors cursor-pointer {searchMode === 'flat' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}"
			onclick={() => switchMode('flat')}
		>
			Token Search
		</button>
		<button
			class="rounded-md px-4 py-1.5 text-sm font-medium transition-colors cursor-pointer {searchMode === 'structural' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}"
			onclick={() => switchMode('structural')}
		>
			Structural Search
		</button>
	</div>

	<!-- Flat (token) search -->
	{#if searchMode === 'flat'}
		<form onsubmit={handleFlatSearch} class="mb-6 space-y-3">
			<div class="flex gap-3 items-end">
				<div class="space-y-1">
					<label for="tb-select" class="text-xs font-medium text-muted-foreground">Treebank</label>
					<select
						id="tb-select"
						bind:value={selectedTreebank}
						class="flex h-9 rounded-md border border-input bg-background px-3 text-sm focus-visible:ring-2 focus-visible:ring-ring"
					>
						<option value="">All treebanks</option>
						{#each treebanks as tb}
							<option value={tb.title}>{tb.title}</option>
						{/each}
					</select>
				</div>
			</div>

			{#each queries as q, i}
				<div class="flex items-center gap-2">
					<select
						value={q.field}
						onchange={(e) => handleFieldChange(i, (e.target as HTMLSelectElement).value)}
						class="flex h-9 rounded-md border border-input bg-background px-2 text-sm focus-visible:ring-2 focus-visible:ring-ring"
					>
						{#each FLAT_FIELD_OPTIONS as opt}
							<option value={opt}>{opt.toUpperCase()}</option>
						{/each}
					</select>

					{#if q.field === 'upos'}
						<SearchAutocomplete
							value={q.value}
							options={UPOS_TAGS}
							onchange={(v) => { q.value = v; }}
							placeholder="Select UPOS tag..."
							class="flex-1"
						/>
					{:else if q.field === 'deprel'}
						<SearchAutocomplete
							value={q.value}
							options={DEPREL_TAGS}
							onchange={(v) => { q.value = v; }}
							placeholder="Select dependency relation..."
							class="flex-1"
						/>
					{:else if q.field === 'feats'}
						<SearchAutocomplete
							value={q.featKey}
							options={FEATURE_KEYS}
							onchange={(v) => { q.featKey = v; q.featValue = ''; }}
							placeholder="Feature name..."
							class="flex-1"
						/>
						<span class="text-muted-foreground">=</span>
						<SearchAutocomplete
							value={q.featValue}
							options={q.featKey && FEATURES[q.featKey] ? FEATURES[q.featKey] : []}
							onchange={(v) => { q.featValue = v; }}
							placeholder={q.featKey ? 'Feature value...' : 'Select a feature first'}
							class="flex-1"
						/>
					{:else if q.field === 'misc'}
						<SearchAutocomplete
							value={q.miscKey}
							options={MISC_KEYS}
							onchange={(v) => { q.miscKey = v; q.miscValue = ''; }}
							placeholder="MISC key..."
							class="flex-1"
						/>
						<span class="text-muted-foreground">=</span>
						{#if q.miscKey && getMiscValueOptions(q.miscKey)}
							<SearchAutocomplete
								value={q.miscValue}
								options={getMiscValueOptions(q.miscKey) ?? []}
								onchange={(v) => { q.miscValue = v; }}
								placeholder="MISC value..."
								class="flex-1"
							/>
						{:else}
							<Input
								bind:value={q.miscValue}
								placeholder={q.miscKey ? 'Value...' : 'Select a key first'}
								class="flex-1"
							/>
						{/if}
					{:else}
						<Input bind:value={q.value} placeholder="Search value..." class="flex-1" />
					{/if}

					{#if queries.length > 1}
						<button onclick={() => removeRow(i)} class="text-muted-foreground hover:text-destructive cursor-pointer">&times;</button>
					{/if}
				</div>
			{/each}

			<div class="flex gap-2">
				<Button variant="outline" size="sm" onclick={addRow}>+ Add condition</Button>
				<Button type="submit" size="sm" disabled={loading}>
					{loading ? 'Searching...' : 'Search'}
				</Button>
			</div>
		</form>

		<!-- Flat results -->
		{#if searched}
			{#if flatResults.length === 0}
				<p class="text-muted-foreground">No results found.</p>
			{:else}
				<div class="overflow-hidden rounded-lg border border-border">
					<table class="w-full text-sm">
						<thead class="bg-muted text-left">
							<tr>
								<th class="px-3 py-2 font-medium">Sent ID</th>
								<th class="px-3 py-2 font-medium">Text</th>
								<th class="px-3 py-2 font-medium">Treebank</th>
								<th class="px-3 py-2 font-medium">FORM</th>
								<th class="px-3 py-2 font-medium">UPOS</th>
								<th class="px-3 py-2 font-medium">DEPREL</th>
							</tr>
						</thead>
						<tbody>
							{#each flatResults as r}
								<tr class="border-t border-border hover:bg-muted/50">
									<td class="px-3 py-2 font-mono text-xs">{r.sentence_sent_id}</td>
									<td class="px-3 py-2 max-w-xs truncate">{r.sentence_text}</td>
									<td class="px-3 py-2 text-muted-foreground">{r.treebank_title}</td>
									<td class="px-3 py-2 font-medium">{r.form}</td>
									<td class="px-3 py-2">{r.upos}</td>
									<td class="px-3 py-2">{r.deprel}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				<div class="mt-4 flex items-center justify-between">
					<Button variant="outline" size="sm" disabled={flatPage === 0} onclick={() => goFlatPage(flatPage - 1)}>
						Previous
					</Button>
					<span class="text-sm text-muted-foreground">
						Showing {flatPage * pageSize + 1}–{flatPage * pageSize + flatResults.length} of {flatTotal} results
					</span>
					<Button variant="outline" size="sm" disabled={flatPage * pageSize + flatResults.length >= flatTotal} onclick={() => goFlatPage(flatPage + 1)}>
						Next
					</Button>
				</div>
			{/if}
		{/if}
	{/if}

	<!-- Structural search -->
	{#if searchMode === 'structural'}
		<div class="mb-6">
			<StructuralQueryBuilder
				onsearch={handleStructuralSearch}
				{loading}
				treebanks={treebanks.map((tb) => ({ id: tb.id, title: tb.title }))}
			/>
		</div>

		<!-- Structural results -->
		{#if searched}
			{#if structuralResults.length === 0}
				<p class="text-muted-foreground">No results found.</p>
			{:else}
				<div class="space-y-3">
					{#each structuralResults as match}
						<div class="rounded-lg border border-border p-4 hover:bg-muted/30 transition-colors">
							<div class="flex items-center justify-between mb-2">
								<div class="flex items-center gap-3">
									<span class="font-mono text-xs text-muted-foreground">{match.sent_id}</span>
									<span class="text-xs text-muted-foreground">{match.treebank_title}</span>
								</div>
								<a
									href="/annotate/{match.treebank_id}/{match.sentence_id}"
									class="text-xs text-primary hover:underline"
								>
									Open in annotator
								</a>
							</div>
							<p class="text-sm leading-relaxed">
								{#each highlightTokens(match.text, match.matched_token_ids) as segment}
									{#if segment.highlighted}
										<mark class="rounded bg-primary/20 px-0.5 font-semibold text-foreground">{segment.text}</mark>
									{:else}
										{segment.text}
									{/if}
								{/each}
							</p>
						</div>
					{/each}
				</div>

				<div class="mt-4 flex items-center justify-between">
					<Button variant="outline" size="sm" disabled={structuralPage === 0} onclick={() => goStructuralPage(structuralPage - 1)}>
						Previous
					</Button>
					<span class="text-sm text-muted-foreground">
						Showing {structuralPage * pageSize + 1}–{structuralPage * pageSize + structuralResults.length} of {structuralTotal} results
					</span>
					<Button variant="outline" size="sm" disabled={structuralPage * pageSize + structuralResults.length >= structuralTotal} onclick={() => goStructuralPage(structuralPage + 1)}>
						Next
					</Button>
				</div>
			{/if}
		{/if}
	{/if}
</div>
