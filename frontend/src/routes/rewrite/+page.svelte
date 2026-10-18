<script lang="ts">
	import { onMount } from 'svelte';
	import { rewritePreview, rewriteApply } from '$api/search';
	import { listTreebanks } from '$api/treebanks';
	import type {
		TreebankWithProgress,
		RewriteChange,
		RewritePreviewResponse,
		RewriteApplyResponse
	} from '$api/types';
	import Button from '$components/common/Button.svelte';
	import { toast } from '$stores/toast';
	import { ApiError } from '$api/client';

	let treebanks = $state<TreebankWithProgress[]>([]);
	let selectedTreebankId = $state<number | undefined>(undefined);
	let scope = $state<'template' | 'mine' | 'all'>('template');
	let pattern = $state('');
	let operationInput = $state('');
	let operations = $state<string[]>([]);

	let loading = $state(false);
	let applying = $state(false);
	let preview = $state<RewritePreviewResponse | null>(null);
	let applied = $state<RewriteApplyResponse | null>(null);

	onMount(async () => {
		try {
			treebanks = await listTreebanks();
		} catch {
			toast.error('Failed to load treebanks');
		}
	});

	function addOperation() {
		const op = operationInput.trim();
		if (op && !operations.includes(op)) {
			operations = [...operations, op];
			operationInput = '';
		}
	}

	function removeOperation(i: number) {
		operations = operations.filter((_, j) => j !== i);
	}

	function handleOperationKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addOperation();
		}
	}

	function buildRequest() {
		return {
			pattern,
			operations,
			treebank_id: selectedTreebankId,
			annotation_scope: scope
		};
	}

	async function handlePreview(e?: SubmitEvent) {
		e?.preventDefault();
		loading = true;
		preview = null;
		applied = null;
		try {
			preview = await rewritePreview(buildRequest());
			if (preview.total_tokens === 0) {
				toast.info('No tokens matched the pattern');
			}
		} catch (err) {
			toast.error(err instanceof ApiError ? err.detail : 'Preview failed');
		} finally {
			loading = false;
		}
	}

	async function handleApply() {
		applying = true;
		try {
			applied = await rewriteApply(buildRequest());
			preview = null;
			toast.success(`Applied changes to ${applied.applied} annotation(s)`);
			if (applied.skipped > 0) {
				toast.info(`Skipped ${applied.skipped} submitted/approved annotation(s)`);
			}
		} catch (err) {
			toast.error(err instanceof ApiError ? err.detail : 'Apply failed');
		} finally {
			applying = false;
		}
	}

	let canSubmit = $derived(pattern.trim().length > 0 && operations.length > 0);
</script>

<div class="mx-auto max-w-5xl px-4 py-8">
	<h1 class="mb-2 text-2xl font-bold">Batch Rewrite</h1>
	<p class="mb-6 text-sm text-muted-foreground">
		Find tokens matching a pattern and apply bulk edits. Changes are previewed before applying.
	</p>

	<form onsubmit={handlePreview} class="mb-8 max-w-2xl space-y-4">
		<!-- Treebank + Scope -->
		<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
			<div class="space-y-1">
				<label for="treebank" class="text-xs font-medium text-muted-foreground">Treebank</label>
				<select
					bind:value={selectedTreebankId}
					id="treebank"
					class="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
				>
					<option value={undefined}>All treebanks</option>
					{#each treebanks as tb}
						<option value={tb.id}>{tb.title}</option>
					{/each}
				</select>
			</div>

			<div class="space-y-1">
				<label for="scope" class="text-xs font-medium text-muted-foreground">Annotation scope</label>
				<select
					bind:value={scope}
					id="scope"
					class="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
				>
					<option value="template">Template annotations</option>
					<option value="mine">My annotations</option>
					<option value="all">All annotations</option>
				</select>
			</div>
		</div>

		<!-- Pattern -->
		<div class="space-y-1">
			<label for="pattern" class="text-xs font-medium text-muted-foreground">Search pattern</label>
			<textarea
				bind:value={pattern}
				id="pattern"
				rows={3}
				placeholder={"Single-node:  UPOS=NOUN & Case=Dat\nStructural:   v: [UPOS=VERB]\n              s: [UPOS=NOUN] -nsubj-> v"}
				class="flex w-full rounded-md border border-input bg-background px-3 py-2 font-mono text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
			></textarea>
			<p class="text-xs text-muted-foreground">
				Supports single-node (<code>UPOS=NOUN & Case=Dat</code>) and structural patterns
				(<code>v: [UPOS=VERB]</code> with relations like <code>-nsubj-></code>).
			</p>
		</div>

		<!-- Operations -->
		<div class="space-y-2">
			<label for="op-input" class="text-xs font-medium text-muted-foreground">Rewrite operations</label>
			<div class="flex gap-2">
				<input
					id="op-input"
					bind:value={operationInput}
					placeholder="e.g. Case=Nom, UPOS=ADJ, -Gender, s.Case=Acc"
					onkeydown={handleOperationKeydown}
					class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
				/>
				<Button type="button" variant="outline" size="sm" onclick={addOperation}>Add</Button>
			</div>
			{#if operations.length > 0}
				<div class="flex flex-wrap gap-2">
					{#each operations as op, i}
						<span
							class="inline-flex items-center gap-1 rounded-md border border-border bg-muted/50 px-2 py-1 font-mono text-xs"
						>
							{op}
							<button
								type="button"
								onclick={() => removeOperation(i)}
								class="cursor-pointer text-muted-foreground hover:text-destructive"
							>&times;</button>
						</span>
					{/each}
				</div>
			{/if}
			<p class="text-xs text-muted-foreground">
				<code>Field=Value</code> to set, <code>-Field</code> to remove.
				Prefix with node name for structural patterns: <code>s.Case=Nom</code>.
			</p>
		</div>

		<!-- Submit -->
		<div class="flex gap-2">
			<Button type="submit" size="sm" disabled={!canSubmit || loading}>
				{loading ? 'Generating preview...' : 'Preview changes'}
			</Button>
		</div>
	</form>

	<!-- Preview results -->
	{#if preview && preview.total_tokens > 0}
		<div class="space-y-4">
			<div class="flex items-center justify-between">
				<h2 class="text-lg font-semibold">
					Preview: {preview.total_tokens} change{preview.total_tokens !== 1 ? 's' : ''}
					in {preview.total_sentences} sentence{preview.total_sentences !== 1 ? 's' : ''}
				</h2>
				<Button
					variant="primary"
					size="sm"
					disabled={applying}
					onclick={handleApply}
				>
					{applying ? 'Applying...' : 'Apply changes'}
				</Button>
			</div>

			<div class="overflow-x-auto rounded-lg border border-border">
				<table class="w-full text-sm">
					<thead class="border-b border-border bg-muted/50">
						<tr>
							<th class="px-3 py-2 text-left font-medium text-muted-foreground">Sentence</th>
							<th class="px-3 py-2 text-left font-medium text-muted-foreground">Token</th>
							<th class="px-3 py-2 text-left font-medium text-muted-foreground">Node</th>
							<th class="px-3 py-2 text-left font-medium text-muted-foreground">Changes</th>
						</tr>
					</thead>
					<tbody>
						{#each preview.changes as change}
							<tr class="border-b border-border/50 last:border-0">
								<td class="px-3 py-2 font-mono text-xs text-muted-foreground">{change.sent_id}</td>
								<td class="px-3 py-2">
									<span class="font-mono text-xs text-muted-foreground">{change.token_id}</span>
									<span class="ml-1">{change.form}</span>
								</td>
								<td class="px-3 py-2 font-mono text-xs">{change.node_name}</td>
								<td class="px-3 py-2">
									{#each change.descriptions as desc}
										<span class="mr-2 inline-block rounded bg-primary/10 px-1.5 py-0.5 font-mono text-xs text-primary">
											{desc}
										</span>
									{/each}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	{/if}

	<!-- Applied results -->
	{#if applied}
		<div class="space-y-4">
			<div class="rounded-lg border border-success/30 bg-success/5 p-4">
				<h2 class="text-lg font-semibold text-success">
					Applied: {applied.applied} annotation{applied.applied !== 1 ? 's' : ''} modified
				</h2>
				{#if applied.skipped > 0}
					<p class="mt-1 text-sm text-muted-foreground">
						{applied.skipped} annotation{applied.skipped !== 1 ? 's' : ''} skipped (submitted/approved).
					</p>
				{/if}
			</div>

			{#if applied.changes.length > 0}
				<div class="overflow-x-auto rounded-lg border border-border">
					<table class="w-full text-sm">
						<thead class="border-b border-border bg-muted/50">
							<tr>
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">Sentence</th>
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">Token</th>
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">Node</th>
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">Changes</th>
							</tr>
						</thead>
						<tbody>
							{#each applied.changes as change}
								<tr class="border-b border-border/50 last:border-0">
									<td class="px-3 py-2 font-mono text-xs text-muted-foreground">{change.sent_id}</td>
									<td class="px-3 py-2">
										<span class="font-mono text-xs text-muted-foreground">{change.token_id}</span>
										<span class="ml-1">{change.form}</span>
									</td>
									<td class="px-3 py-2 font-mono text-xs">{change.node_name}</td>
									<td class="px-3 py-2">
										{#each change.descriptions as desc}
											<span class="mr-2 inline-block rounded bg-success/10 px-1.5 py-0.5 font-mono text-xs text-success">
												{desc}
											</span>
										{/each}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	{/if}
</div>
