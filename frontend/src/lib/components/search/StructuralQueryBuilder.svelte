<script lang="ts">
	import { UPOS_TAGS, DEPREL_TAGS, FEATURES } from '$utils/ud-tagsets';
	import type { NodeConstraint, RelationConstraint, StructuralQuery } from '$api/types';
	import SearchAutocomplete from '$components/common/SearchAutocomplete.svelte';
	import Input from '$components/common/Input.svelte';
	import Button from '$components/common/Button.svelte';

	interface Props {
		onsearch: (query: StructuralQuery) => void;
		loading?: boolean;
		treebanks: { id: number; title: string }[];
	}

	let { onsearch, loading = false, treebanks }: Props = $props();

	const FEATURE_KEYS = Object.keys(FEATURES);

	// --- Target token state ---
	let targetUpos = $state('');
	let targetForm = $state('');
	let targetLemma = $state('');
	let targetFeatKey = $state('');
	let targetFeatValue = $state('');

	// --- Head constraint state ---
	let headEnabled = $state(false);
	let headExpanded = $state(false);
	let headDeprel = $state('');
	let headUpos = $state('');
	let headFeatKey = $state('');
	let headFeatValue = $state('');

	// --- Dependent constraints ---
	interface DepRow {
		deprel: string;
		upos: string;
		featKey: string;
		featValue: string;
	}

	function makeDepRow(): DepRow {
		return { deprel: '', upos: '', featKey: '', featValue: '' };
	}

	let dependents = $state<DepRow[]>([]);
	let depsExpanded = $state(false);

	// --- Negated dependents ---
	let negatedDeps = $state<DepRow[]>([]);
	let negDepsExpanded = $state(false);

	// --- Treebank filter ---
	let selectedTreebankId = $state('');

	// --- Build query ---
	function buildNodeConstraint(
		upos: string,
		form: string,
		lemma: string,
		featKey: string,
		featValue: string
	): NodeConstraint {
		const c: NodeConstraint = {};
		if (upos) c.upos = [upos];
		if (form.trim()) c.form = form.trim();
		if (lemma.trim()) c.lemma = lemma.trim();
		if (featKey && featValue) {
			c.feats = { [featKey]: [featValue] };
		}
		return c;
	}

	function buildRelationConstraint(row: DepRow): RelationConstraint {
		const c: RelationConstraint = {};
		if (row.deprel) c.deprel = [row.deprel];
		if (row.upos) c.upos = [row.upos];
		if (row.featKey && row.featValue) {
			c.feats = { [row.featKey]: [row.featValue] };
		}
		return c;
	}

	function isConstraintEmpty(c: NodeConstraint | RelationConstraint): boolean {
		return (
			!c.upos?.length &&
			!c.form &&
			!c.lemma &&
			!c.feats &&
			!(c as RelationConstraint).deprel?.length
		);
	}

	function handleSubmit(e?: SubmitEvent) {
		e?.preventDefault();

		const target = buildNodeConstraint(targetUpos, targetForm, targetLemma, targetFeatKey, targetFeatValue);
		const query: StructuralQuery = { target };

		if (headEnabled) {
			const hc: RelationConstraint = {};
			if (headDeprel) hc.deprel = [headDeprel];
			if (headUpos) hc.upos = [headUpos];
			if (headFeatKey && headFeatValue) {
				hc.feats = { [headFeatKey]: [headFeatValue] };
			}
			if (!isConstraintEmpty(hc)) {
				query.head_constraint = hc;
			}
		}

		const depConstraints = dependents
			.map(buildRelationConstraint)
			.filter((c) => !isConstraintEmpty(c));
		if (depConstraints.length > 0) {
			query.dependent_constraints = depConstraints;
		}

		const negConstraints = negatedDeps
			.map(buildRelationConstraint)
			.filter((c) => !isConstraintEmpty(c));
		if (negConstraints.length > 0) {
			query.negated_dependents = negConstraints;
		}

		if (selectedTreebankId) {
			query.treebank_id = Number(selectedTreebankId);
		}

		onsearch(query);
	}

	function toggleSection(section: 'head' | 'deps' | 'negDeps') {
		if (section === 'head') headExpanded = !headExpanded;
		else if (section === 'deps') depsExpanded = !depsExpanded;
		else negDepsExpanded = !negDepsExpanded;
	}
</script>

<form onsubmit={handleSubmit} class="space-y-4">
	<!-- Treebank filter -->
	<div class="space-y-1">
		<label for="structural-tb" class="text-xs font-medium text-muted-foreground">Treebank</label>
		<select
			id="structural-tb"
			bind:value={selectedTreebankId}
			class="flex h-9 rounded-md border border-input bg-background px-3 text-sm focus-visible:ring-2 focus-visible:ring-ring"
		>
			<option value="">All treebanks</option>
			{#each treebanks as tb}
				<option value={tb.id}>{tb.title}</option>
			{/each}
		</select>
	</div>

	<!-- Target token section -->
	<fieldset class="rounded-lg border border-border p-4 space-y-3">
		<legend class="px-2 text-sm font-semibold text-foreground">Find tokens where</legend>

		<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
			<div class="space-y-1">
				<label class="text-xs font-medium text-muted-foreground">UPOS</label>
				<SearchAutocomplete
					value={targetUpos}
					options={UPOS_TAGS}
					onchange={(v) => { targetUpos = v; }}
					placeholder="Any part of speech..."
				/>
			</div>
			<div class="space-y-1">
				<label class="text-xs font-medium text-muted-foreground">FORM</label>
				<Input bind:value={targetForm} placeholder="Word form..." />
			</div>
			<div class="space-y-1">
				<label class="text-xs font-medium text-muted-foreground">LEMMA</label>
				<Input bind:value={targetLemma} placeholder="Lemma..." />
			</div>
			<div class="space-y-1">
				<label class="text-xs font-medium text-muted-foreground">FEATS</label>
				<div class="flex items-center gap-1">
					<SearchAutocomplete
						value={targetFeatKey}
						options={FEATURE_KEYS}
						onchange={(v) => { targetFeatKey = v; targetFeatValue = ''; }}
						placeholder="Feature..."
						class="flex-1"
					/>
					<span class="text-muted-foreground">=</span>
					<SearchAutocomplete
						value={targetFeatValue}
						options={targetFeatKey && FEATURES[targetFeatKey] ? FEATURES[targetFeatKey] : []}
						onchange={(v) => { targetFeatValue = v; }}
						placeholder={targetFeatKey ? 'Value...' : 'Select feature first'}
						class="flex-1"
					/>
				</div>
			</div>
		</div>
	</fieldset>

	<!-- Head constraint section -->
	<fieldset class="rounded-lg border border-border p-4 space-y-3">
		<legend class="px-2 text-sm font-semibold text-foreground">
			<button
				type="button"
				class="flex items-center gap-2 cursor-pointer"
				onclick={() => toggleSection('head')}
			>
				<span class="text-xs text-muted-foreground transition-transform {headExpanded ? 'rotate-90' : ''}"
					>&#9654;</span
				>
				Its head is
				{#if !headEnabled}
					<span class="text-xs font-normal text-muted-foreground">(disabled)</span>
				{/if}
			</button>
		</legend>

		{#if headExpanded}
			<div class="flex items-center gap-2 mb-2">
				<label class="flex items-center gap-2 text-sm cursor-pointer">
					<input type="checkbox" bind:checked={headEnabled} class="accent-primary" />
					Enable head constraint
				</label>
			</div>

			{#if headEnabled}
				<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
					<div class="space-y-1">
						<label class="text-xs font-medium text-muted-foreground">DEPREL (relation to head)</label>
						<SearchAutocomplete
							value={headDeprel}
							options={DEPREL_TAGS}
							onchange={(v) => { headDeprel = v; }}
							placeholder="Dependency relation..."
						/>
					</div>
					<div class="space-y-1">
						<label class="text-xs font-medium text-muted-foreground">Head UPOS</label>
						<SearchAutocomplete
							value={headUpos}
							options={UPOS_TAGS}
							onchange={(v) => { headUpos = v; }}
							placeholder="Head part of speech..."
						/>
					</div>
					<div class="space-y-1 sm:col-span-2">
						<label class="text-xs font-medium text-muted-foreground">Head FEATS</label>
						<div class="flex items-center gap-1">
							<SearchAutocomplete
								value={headFeatKey}
								options={FEATURE_KEYS}
								onchange={(v) => { headFeatKey = v; headFeatValue = ''; }}
								placeholder="Feature..."
								class="flex-1"
							/>
							<span class="text-muted-foreground">=</span>
							<SearchAutocomplete
								value={headFeatValue}
								options={headFeatKey && FEATURES[headFeatKey] ? FEATURES[headFeatKey] : []}
								onchange={(v) => { headFeatValue = v; }}
								placeholder={headFeatKey ? 'Value...' : 'Select feature first'}
								class="flex-1"
							/>
						</div>
					</div>
				</div>
			{/if}
		{/if}
	</fieldset>

	<!-- Dependent constraints section -->
	<fieldset class="rounded-lg border border-border p-4 space-y-3">
		<legend class="px-2 text-sm font-semibold text-foreground">
			<button
				type="button"
				class="flex items-center gap-2 cursor-pointer"
				onclick={() => toggleSection('deps')}
			>
				<span class="text-xs text-muted-foreground transition-transform {depsExpanded ? 'rotate-90' : ''}"
					>&#9654;</span
				>
				Must have dependent
				{#if dependents.length > 0}
					<span class="text-xs font-normal text-muted-foreground">({dependents.length})</span>
				{/if}
			</button>
		</legend>

		{#if depsExpanded}
			{#each dependents as dep, i}
				<div class="flex items-start gap-2 rounded-md border border-border/50 bg-muted/30 p-3">
					<div class="grid flex-1 grid-cols-1 gap-2 sm:grid-cols-3">
						<div class="space-y-1">
							<label class="text-xs font-medium text-muted-foreground">DEPREL</label>
							<SearchAutocomplete
								value={dep.deprel}
								options={DEPREL_TAGS}
								onchange={(v) => { dep.deprel = v; }}
								placeholder="Relation..."
							/>
						</div>
						<div class="space-y-1">
							<label class="text-xs font-medium text-muted-foreground">UPOS</label>
							<SearchAutocomplete
								value={dep.upos}
								options={UPOS_TAGS}
								onchange={(v) => { dep.upos = v; }}
								placeholder="Part of speech..."
							/>
						</div>
						<div class="space-y-1">
							<label class="text-xs font-medium text-muted-foreground">FEATS</label>
							<div class="flex items-center gap-1">
								<SearchAutocomplete
									value={dep.featKey}
									options={FEATURE_KEYS}
									onchange={(v) => { dep.featKey = v; dep.featValue = ''; }}
									placeholder="Feat..."
									class="flex-1"
								/>
								<span class="text-muted-foreground">=</span>
								<SearchAutocomplete
									value={dep.featValue}
									options={dep.featKey && FEATURES[dep.featKey] ? FEATURES[dep.featKey] : []}
									onchange={(v) => { dep.featValue = v; }}
									placeholder="Val..."
									class="flex-1"
								/>
							</div>
						</div>
					</div>
					<button
						type="button"
						onclick={() => { dependents = dependents.filter((_, j) => j !== i); }}
						class="mt-5 text-muted-foreground hover:text-destructive cursor-pointer"
					>&times;</button>
				</div>
			{/each}

			<Button
				variant="outline"
				size="sm"
				onclick={() => { dependents = [...dependents, makeDepRow()]; }}
			>+ Add dependent constraint</Button>
		{/if}
	</fieldset>

	<!-- Negated dependent section -->
	<fieldset class="rounded-lg border border-border p-4 space-y-3">
		<legend class="px-2 text-sm font-semibold text-foreground">
			<button
				type="button"
				class="flex items-center gap-2 cursor-pointer"
				onclick={() => toggleSection('negDeps')}
			>
				<span class="text-xs text-muted-foreground transition-transform {negDepsExpanded ? 'rotate-90' : ''}"
					>&#9654;</span
				>
				Must NOT have dependent
				{#if negatedDeps.length > 0}
					<span class="text-xs font-normal text-muted-foreground">({negatedDeps.length})</span>
				{/if}
			</button>
		</legend>

		{#if negDepsExpanded}
			{#each negatedDeps as dep, i}
				<div class="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/5 p-3">
					<div class="grid flex-1 grid-cols-1 gap-2 sm:grid-cols-2">
						<div class="space-y-1">
							<label class="text-xs font-medium text-muted-foreground">DEPREL</label>
							<SearchAutocomplete
								value={dep.deprel}
								options={DEPREL_TAGS}
								onchange={(v) => { dep.deprel = v; }}
								placeholder="Relation..."
							/>
						</div>
						<div class="space-y-1">
							<label class="text-xs font-medium text-muted-foreground">UPOS</label>
							<SearchAutocomplete
								value={dep.upos}
								options={UPOS_TAGS}
								onchange={(v) => { dep.upos = v; }}
								placeholder="Part of speech..."
							/>
						</div>
					</div>
					<button
						type="button"
						onclick={() => { negatedDeps = negatedDeps.filter((_, j) => j !== i); }}
						class="mt-5 text-muted-foreground hover:text-destructive cursor-pointer"
					>&times;</button>
				</div>
			{/each}

			<Button
				variant="outline"
				size="sm"
				onclick={() => { negatedDeps = [...negatedDeps, makeDepRow()]; }}
			>+ Add exclusion</Button>
		{/if}
	</fieldset>

	<!-- Search button -->
	<div class="flex gap-2">
		<Button type="submit" size="sm" disabled={loading}>
			{loading ? 'Searching...' : 'Search'}
		</Button>
	</div>
</form>
