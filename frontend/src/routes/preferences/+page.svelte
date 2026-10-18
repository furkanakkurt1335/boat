<script lang="ts">
	import { user, updatePreferences } from '$stores/auth';
	import { GRAPH_OPTIONS, ALL_COLUMNS, DEFAULT_COLUMNS } from '$stores/preferences';
	import Button from '$components/common/Button.svelte';

	let graphPref = $state($user?.preferences?.graph_preference ?? 1);
	let errorCond = $state($user?.preferences?.error_condition ?? true);
	let columns = $state<string[]>($user?.preferences?.current_columns ?? [...DEFAULT_COLUMNS]);
	let saving = $state(false);
	let saved = $state(false);

	function toggleColumn(col: string) {
		if (col === 'ID' || col === 'FORM') return;
		columns = columns.includes(col)
			? columns.filter((c) => c !== col)
			: [...columns, col];
	}

	async function handleSave() {
		saving = true;
		saved = false;
		await updatePreferences({
			graph_preference: graphPref,
			error_condition: errorCond,
			current_columns: columns
		});
		saving = false;
		saved = true;
		setTimeout(() => (saved = false), 2000);
	}
</script>

<div class="mx-auto max-w-2xl px-4 py-8">
	<h1 class="mb-6 text-2xl font-bold">Preferences</h1>

	<div class="space-y-6">
		<!-- Graph visualization -->
		<div class="space-y-2">
			<label for="graph-pref" class="text-sm font-medium">Graph visualization</label>
			<select
				id="graph-pref"
				bind:value={graphPref}
				class="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm focus-visible:ring-2 focus-visible:ring-ring"
			>
				{#each GRAPH_OPTIONS as opt}
					<option value={opt.value}>{opt.label}</option>
				{/each}
			</select>
		</div>

		<!-- Error condition -->
		<div class="flex items-center gap-3">
			<input
				id="error-cond"
				type="checkbox"
				bind:checked={errorCond}
				class="h-4 w-4 rounded border-border"
			/>
			<label for="error-cond" class="text-sm font-medium">Show validation errors</label>
		</div>

		<!-- Default columns -->
		<div class="space-y-2">
			<p class="text-sm font-medium">Default visible columns</p>
			<div class="flex flex-wrap gap-2">
				{#each ALL_COLUMNS as col}
					{@const active = columns.includes(col)}
					{@const locked = col === 'ID' || col === 'FORM'}
					<button
						onclick={() => toggleColumn(col)}
						disabled={locked}
						class="rounded-full px-3 py-1 text-xs font-medium transition-colors cursor-pointer
							{active ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}
							{locked ? 'opacity-60 cursor-default' : 'hover:opacity-80'}"
					>
						{col}
					</button>
				{/each}
			</div>
		</div>

		<div class="flex items-center gap-3">
			<Button onclick={handleSave} disabled={saving}>
				{saving ? 'Saving...' : 'Save preferences'}
			</Button>
			{#if saved}
				<span class="text-sm text-success">Saved!</span>
			{/if}
		</div>
	</div>
</div>
