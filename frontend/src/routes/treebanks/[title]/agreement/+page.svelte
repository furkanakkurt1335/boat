<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { getTreebankByTitle, getAgreement } from '$api/treebanks';
	import { listSentences, getSentenceDiff } from '$api/sentences';
	import type { TreebankRead, SentenceBrief, AgreementResponse, DiffResponse } from '$api/types';
	import DiffView from '$components/graph/DiffView.svelte';
	import Breadcrumb from '$components/layout/Breadcrumb.svelte';

	const treebankTitle = $derived(decodeURIComponent(page.params.title!));

	let treebank = $state<TreebankRead | null>(null);
	let sentences = $state<SentenceBrief[]>([]);
	let agreement = $state<AgreementResponse | null>(null);
	let loading = $state(true);
	let error = $state('');

	// Diff for selected sentence
	let selectedSentence = $state<SentenceBrief | null>(null);
	let diff = $state<DiffResponse | null>(null);
	let diffLoading = $state(false);

	onMount(async () => {
		try {
			const tb = await getTreebankByTitle(treebankTitle);
			treebank = tb;
			const [sents, agr] = await Promise.all([
				listSentences(tb.id),
				getAgreement(tb.id)
			]);
			sentences = sents;
			agreement = agr;
		} catch (err) {
			error = String(err);
		} finally {
			loading = false;
		}
	});

	async function viewDiff(sent: SentenceBrief) {
		selectedSentence = sent;
		diffLoading = true;
		try {
			diff = await getSentenceDiff(sent.id);
		} catch {
			diff = null;
		} finally {
			diffLoading = false;
		}
	}
</script>

<div class="mx-auto max-w-7xl px-4 py-8">
	<div class="mb-2">
		<Breadcrumb crumbs={[{ label: 'Treebanks', href: '/treebanks' }, { label: treebank?.title ?? '...', href: `/treebanks/${treebankTitle}` }, { label: 'Agreement' }]} />
	</div>
	<h1 class="mb-6 text-2xl font-bold">Inter-Annotator Agreement</h1>

	{#if loading}
		<p class="text-muted-foreground">Computing agreement...</p>
	{:else if error}
		<div class="rounded-md bg-destructive/10 p-4 text-destructive">{error}</div>
	{:else}
		<!-- Overall score -->
		<div class="mb-6 rounded-lg border border-border p-5">
			<p class="text-sm text-muted-foreground">Overall agreement score</p>
			<p class="text-4xl font-bold">
				{agreement && agreement.sentences_scored > 0 ? agreement.agreement.toFixed(3) : 'N/A'}
			</p>
			<p class="text-xs text-muted-foreground mt-1">
				{agreement?.sentences_scored ?? 0} sentences scored. Averaged across UPOS, FEATS, HEAD, DEPREL.
			</p>
		</div>

		<!-- Per-sentence breakdown -->
		<h2 class="mb-3 text-lg font-semibold">Per-sentence comparison</h2>
		<p class="mb-3 text-sm text-muted-foreground">Click a sentence to view the side-by-side diff between annotators.</p>

		<div class="grid gap-2 lg:grid-cols-3">
			<!-- Sentence list -->
			<div class="lg:col-span-1 space-y-1 max-h-[60vh] overflow-auto">
				{#each sentences as sent}
					{@const isSelected = selectedSentence?.id === sent.id}
					<button
						onclick={() => viewDiff(sent)}
						class="w-full text-left rounded-md border px-3 py-2 text-xs transition-colors cursor-pointer
							{isSelected ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted/50'}"
					>
						<span class="font-mono text-muted-foreground">{sent.sent_id}</span>
						<span class="ml-2 truncate">{sent.text}</span>
					</button>
				{/each}
			</div>

			<!-- Diff view -->
			<div class="lg:col-span-2">
				{#if selectedSentence}
					<div class="rounded-lg border border-border p-4">
						<h3 class="mb-1 text-sm font-semibold">{selectedSentence.sent_id}</h3>
						<p class="mb-3 text-xs text-muted-foreground">{selectedSentence.text}</p>
						{#if diffLoading}
							<p class="text-xs text-muted-foreground">Loading diff...</p>
						{:else if diff}
							<DiffView tokens={diff.tokens} />
						{:else}
							<p class="text-xs text-muted-foreground">Need at least 2 annotations to compare.</p>
						{/if}
					</div>
				{:else}
					<div class="flex h-40 items-center justify-center rounded-lg border border-dashed border-border">
						<p class="text-sm text-muted-foreground">Select a sentence to view the diff</p>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
