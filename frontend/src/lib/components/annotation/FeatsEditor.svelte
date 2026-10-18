<script lang="ts">
	import { FEATURES, DEFAULT_MISC } from '$utils/ud-tagsets';
	import Button from '$components/common/Button.svelte';

	interface Props {
		value: string;
		field?: 'feats' | 'misc';
		allowedFeatures?: Record<string, string[]> | null;
		allowedMisc?: Record<string, string[] | null> | null;
		featureOrder?: string[] | null;
		onchange: (value: string) => void;
		onclose: () => void;
	}

	let { value, field = 'feats', allowedFeatures = null, allowedMisc = null, featureOrder = null, onchange, onclose }: Props = $props();
	const isMisc = $derived(field === 'misc');

	// Resolve effective presets
	const effectiveFeatures = $derived(allowedFeatures ?? FEATURES);
	const effectiveMisc = $derived(allowedMisc ?? DEFAULT_MISC);

	// Feature keys in display order
	const orderedFeatureKeys = $derived(() => {
		const allKeys = Object.keys(effectiveFeatures);
		if (featureOrder && featureOrder.length > 0) {
			const ordered = featureOrder.filter((k) => k in effectiveFeatures);
			const remaining = allKeys.filter((k) => !featureOrder.includes(k)).sort();
			return [...ordered, ...remaining];
		}
		return allKeys.sort();
	});

	// Parse initial FEATS string into a map
	function parseFeats(raw: string): Map<string, string> {
		const m = new Map<string, string>();
		if (raw === '_' || !raw) return m;
		for (const pair of raw.split('|')) {
			const [k, v] = pair.split('=');
			if (k && v) m.set(k, v);
		}
		return m;
	}

	let feats = $state<Map<string, string>>(new Map());

	// Parse when value prop changes (e.g., opened for a different cell)
	$effect(() => {
		feats = parseFeats(value);
	});

	function setFeat(key: string, val: string) {
		const next = new Map(feats);
		if (val === '') {
			next.delete(key);
		} else {
			next.set(key, val);
		}
		feats = next;
	}

	function apply() {
		if (feats.size === 0) {
			onchange('_');
		} else {
			// Sort features alphabetically by key (UD convention)
			const sorted = [...feats.entries()].sort((a, b) => a[0].localeCompare(b[0]));
			onchange(sorted.map(([k, v]) => `${k}=${v}`).join('|'));
		}
		onclose();
	}

	function clear() {
		feats = new Map();
	}

	// For free-form add (both FEATS and MISC)
	let newKey = $state('');
	let newVal = $state('');
	function addEntry() {
		if (newKey.trim() && newVal.trim()) {
			const next = new Map(feats);
			next.set(newKey.trim(), newVal.trim());
			feats = next;
			newKey = '';
			newVal = '';
		}
	}

	function removeEntry(key: string) {
		const next = new Map(feats);
		next.delete(key);
		feats = next;
	}

	// Compute extra (non-preset) keys currently set on the token
	const extraFeatureKeys = $derived(
		[...feats.keys()].filter((k) => !(k in effectiveFeatures)).sort()
	);

	// For MISC: split entries into preset vs extra
	const miscPresetKeys = $derived(Object.keys(effectiveMisc));
	const extraMiscKeys = $derived(
		[...feats.keys()].filter((k) => !(k in effectiveMisc)).sort()
	);
</script>

<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" role="dialog" aria-modal="true" aria-label="Edit features">
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div class="w-full max-w-md rounded-lg bg-background p-4 shadow-lg" onclick={(e) => e.stopPropagation()}>
		<div class="mb-3 flex items-center justify-between">
			<h3 class="text-sm font-semibold">{isMisc ? 'Edit MISC' : 'Edit Features'}</h3>
			<div class="flex gap-2">
				<button onclick={clear} class="text-xs text-muted-foreground hover:text-foreground cursor-pointer">Clear all</button>
				<button onclick={onclose} class="text-muted-foreground hover:text-foreground cursor-pointer">&times;</button>
			</div>
		</div>

		<div class="max-h-80 overflow-auto">
			{#if isMisc}
				<!-- MISC: preset entries -->
				<div class="space-y-1.5">
					{#each miscPresetKeys as key}
						{@const presetValues = effectiveMisc[key]}
						{@const currentVal = feats.get(key) ?? ''}
						<div class="flex items-center gap-1.5">
							<span class="text-xs font-medium w-24 text-right text-muted-foreground shrink-0">{key}</span>
							{#if presetValues}
								<!-- Dropdown for keys with predefined values -->
								<select
									value={currentVal}
									onchange={(e) => setFeat(key, (e.target as HTMLSelectElement).value)}
									class="flex-1 h-7 rounded border border-input bg-background px-1 text-xs focus-visible:ring-2 focus-visible:ring-ring {currentVal ? 'text-foreground' : 'text-muted-foreground'}"
								>
									<option value="">--</option>
									{#each presetValues as val}
										<option value={val}>{val}</option>
									{/each}
								</select>
							{:else}
								<!-- Text input for free-form value keys -->
								<input
									type="text"
									value={currentVal}
									oninput={(e) => setFeat(key, (e.target as HTMLInputElement).value)}
									placeholder="(free-form)"
									class="flex-1 h-7 rounded border border-input bg-background px-2 text-xs focus-visible:ring-2 focus-visible:ring-ring"
								/>
							{/if}
							{#if currentVal}
								<button onclick={() => removeEntry(key)} class="text-xs text-muted-foreground hover:text-destructive cursor-pointer px-1">&times;</button>
							{/if}
						</div>
					{/each}

					<!-- Extra (non-preset) entries already on the token -->
					{#if extraMiscKeys.length > 0}
						<div class="border-t border-border pt-1.5 mt-1.5">
							<span class="text-[10px] uppercase tracking-wider text-muted-foreground">Custom</span>
						</div>
						{#each extraMiscKeys as key}
							<div class="flex items-center gap-1.5">
								<span class="text-xs font-medium w-24 text-right text-muted-foreground shrink-0">{key}</span>
								<input
									type="text"
									value={feats.get(key) ?? ''}
									onchange={(e) => setFeat(key, (e.target as HTMLInputElement).value)}
									class="flex-1 h-7 rounded border border-input bg-background px-2 text-xs focus-visible:ring-2 focus-visible:ring-ring"
								/>
								<button onclick={() => removeEntry(key)} class="text-xs text-muted-foreground hover:text-destructive cursor-pointer px-1">&times;</button>
							</div>
						{/each}
					{/if}

					<!-- Add new arbitrary entry -->
					<div class="flex items-center gap-1.5 pt-1 border-t border-border">
						<input
							type="text"
							bind:value={newKey}
							placeholder="Key"
							class="w-24 h-7 rounded border border-input bg-background px-2 text-xs focus-visible:ring-2 focus-visible:ring-ring"
						/>
						<input
							type="text"
							bind:value={newVal}
							placeholder="Value"
							class="flex-1 h-7 rounded border border-input bg-background px-2 text-xs focus-visible:ring-2 focus-visible:ring-ring"
						/>
						<button onclick={addEntry} class="text-xs text-muted-foreground hover:text-foreground cursor-pointer px-1">+</button>
					</div>
				</div>
			{:else}
				<!-- FEATS: predefined UD features with dropdowns -->
				<div class="grid grid-cols-2 gap-2">
					{#each orderedFeatureKeys() as key}
						{@const currentVal = feats.get(key) ?? ''}
						<div class="flex items-center gap-1.5">
							<label for="feat-{key}" class="text-xs font-medium w-24 text-right text-muted-foreground shrink-0">{key}</label>
							<select
								id="feat-{key}"
								value={currentVal}
								onchange={(e) => setFeat(key, (e.target as HTMLSelectElement).value)}
								class="flex-1 h-7 rounded border border-input bg-background px-1 text-xs focus-visible:ring-2 focus-visible:ring-ring {currentVal ? 'text-foreground' : 'text-muted-foreground'}"
							>
								<option value="">--</option>
								{#each effectiveFeatures[key] as val}
									<option value={val}>{val}</option>
								{/each}
							</select>
						</div>
					{/each}
				</div>

				<!-- Extra features not in the predefined list -->
				{#if extraFeatureKeys.length > 0}
					<div class="border-t border-border pt-2 mt-2">
						<span class="text-[10px] uppercase tracking-wider text-muted-foreground">Custom features</span>
						<div class="mt-1.5 space-y-1.5">
							{#each extraFeatureKeys as key}
								<div class="flex items-center gap-1.5">
									<span class="text-xs font-medium w-24 text-right text-muted-foreground shrink-0">{key}</span>
									<input
										type="text"
										value={feats.get(key) ?? ''}
										onchange={(e) => setFeat(key, (e.target as HTMLInputElement).value)}
										class="flex-1 h-7 rounded border border-input bg-background px-2 text-xs focus-visible:ring-2 focus-visible:ring-ring"
									/>
									<button onclick={() => removeEntry(key)} class="text-xs text-muted-foreground hover:text-destructive cursor-pointer px-1">&times;</button>
								</div>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Free-form add for unregistered features -->
				<div class="flex items-center gap-1.5 pt-2 mt-2 border-t border-border">
					<input
						type="text"
						bind:value={newKey}
						placeholder="Feature"
						class="w-24 h-7 rounded border border-input bg-background px-2 text-xs focus-visible:ring-2 focus-visible:ring-ring"
					/>
					<input
						type="text"
						bind:value={newVal}
						placeholder="Value"
						class="flex-1 h-7 rounded border border-input bg-background px-2 text-xs focus-visible:ring-2 focus-visible:ring-ring"
					/>
					<button onclick={addEntry} class="text-xs text-muted-foreground hover:text-foreground cursor-pointer px-1">+</button>
				</div>
			{/if}
		</div>

		<!-- Current string preview -->
		<div class="mt-3 rounded bg-muted px-2 py-1">
			<code class="text-xs">
				{feats.size === 0 ? '_' : [...feats.entries()].sort((a, b) => a[0].localeCompare(b[0])).map(([k, v]) => `${k}=${v}`).join('|')}
			</code>
		</div>

		<div class="mt-3 flex justify-end gap-2">
			<Button variant="ghost" size="sm" onclick={onclose}>Cancel</Button>
			<Button size="sm" onclick={apply}>Apply</Button>
		</div>
	</div>
</div>
