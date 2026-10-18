<script lang="ts">
	import { cells, initialCells, updateCell, addRow, removeRow, COLUMN_LABELS, type CellField } from '$stores/annotation';
	import AnnotationCell from './AnnotationCell.svelte';
	import SearchableSelect from './SearchableSelect.svelte';
	import FeatsEditor from './FeatsEditor.svelte';
	import { UPOS_TAGS, DEPREL_TAGS } from '$utils/ud-tagsets';
	import type { ValidationProfileRead } from '$api/types';

	interface Props {
		visibleColumns: string[];
		selectedTokenId?: string | null;
		validationProfile?: ValidationProfileRead | null;
		validationErrors?: Map<string, string[]>;
		onTokenSelect?: (tokenId: string) => void;
	}

	let { visibleColumns, selectedTokenId = null, validationProfile = null, validationErrors = new Map(), onTokenSelect }: Props = $props();

	const allColumns = ['id_f', 'form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc'];
	const editableFields: CellField[] = ['form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc'];

	const columns = $derived(allColumns.filter((c) => visibleColumns.includes(c.toUpperCase()) || c === 'id_f'));

	// FEATS/MISC editor state
	let featsEditToken = $state<string | null>(null);
	let featsEditValue = $state('');
	let featsEditField = $state<'feats' | 'misc'>('feats');

	function handleCellChange(tokenId: string, field: CellField, value: string) {
		updateCell(tokenId, field, value);
	}

	function handleSelectChange(tokenId: string, field: CellField, value: string) {
		updateCell(tokenId, field, value);
	}

	function openFeatsEditor(tokenId: string, currentValue: string, field: 'feats' | 'misc' = 'feats') {
		featsEditToken = tokenId;
		featsEditValue = currentValue;
		featsEditField = field;
	}

	function handleFeatsApply(value: string) {
		if (featsEditToken) {
			updateCell(featsEditToken, featsEditField, value);
		}
		featsEditToken = null;
	}

	function isEditable(col: string): col is CellField {
		return editableFields.includes(col as CellField);
	}

	// Enable native browser virtualization for long sentences (100+ tokens)
	const isLongSentence = $derived($cells.length > 100);

	// Look up validation errors for a given cell and column
	function cellErrors(cellId: string, col: string): string[] | null {
		const key = `${cellId}:${col}`;
		const msgs = validationErrors.get(key);
		return msgs && msgs.length > 0 ? msgs : null;
	}

	// Build a lookup from initial cells for diff highlighting
	const initialMap = $derived(
		new Map($initialCells.map((c) => [c.id_f, c]))
	);

	function isCellChanged(cell: typeof $cells[0], col: string): boolean {
		if (col === 'id_f') return false;
		const init = initialMap.get(cell.id_f);
		if (!init) return false;
		return cell[col as CellField] !== init[col as CellField];
	}
</script>

<div class="overflow-x-auto" class:annotation-table-scroll={isLongSentence}>
	<table class="w-full border-collapse text-sm" role="grid" aria-label="Annotation table">
		<thead>
			<tr class="bg-muted">
				{#each columns as col}
					<th class="border-r border-b-2 border-border px-2 py-1.5 text-left text-xs font-semibold uppercase tracking-wider">
						{COLUMN_LABELS[col] ?? col}
					</th>
				{/each}
				<th class="w-16 border-b-2 border-border px-2 py-1.5 text-xs font-semibold"></th>
			</tr>
		</thead>
		<tbody>
			{#each $cells as cell, idx (cell.id_f)}
				{@const isMultiword = cell.id_f.includes('-')}
				{@const isSelected = cell.id_f === selectedTokenId}
				{@const isEven = idx % 2 === 0}
				<tr
					class="border-t border-border hover:bg-muted/30 {isMultiword ? 'opacity-70' : ''} {isSelected ? 'bg-blue-50 dark:bg-blue-950/30' : isEven ? 'bg-muted/20' : ''}"
					style={isLongSentence ? 'content-visibility: auto; contain-intrinsic-size: auto 32px;' : ''}
					onclick={() => onTokenSelect?.(cell.id_f)}
				>
					{#each columns as col}
						{@const errors = cellErrors(cell.id_f, col)}
						{@const changed = isCellChanged(cell, col)}
						{#if col === 'id_f'}
							<td class="border-r border-border px-2 py-1 text-xs font-mono text-muted-foreground">
								{cell.id_f}
							</td>
						{:else if col === 'upos'}
							<SearchableSelect
								value={cell.upos}
								options={UPOS_TAGS}
								onchange={(v) => handleSelectChange(cell.id_f, 'upos', v)}
								class="{errors ? 'ring-2 ring-destructive/50' : ''} {changed ? 'bg-blue-50 dark:bg-blue-950/30' : ''}"
								title={errors ? errors.join('; ') : undefined}
							/>
						{:else if col === 'deprel'}
							<SearchableSelect
								value={cell.deprel}
								options={DEPREL_TAGS}
								onchange={(v) => handleSelectChange(cell.id_f, 'deprel', v)}
								class="{errors ? 'ring-2 ring-destructive/50' : ''} {changed ? 'bg-blue-50 dark:bg-blue-950/30' : ''}"
								title={errors ? errors.join('; ') : undefined}
							/>
						{:else if col === 'feats'}
							<td class="border-r border-border px-1 py-0.5 {changed ? 'bg-blue-50 dark:bg-blue-950/30' : ''} {errors ? 'border-b-2 border-b-destructive' : ''}" title={errors ? errors.join('; ') : undefined}>
								<button
									onclick={() => openFeatsEditor(cell.id_f, cell.feats, 'feats')}
									class="w-full text-left rounded px-1 py-0.5 text-xs outline-none hover:bg-muted cursor-pointer truncate max-w-[10rem]"
									title={cell.feats}
								>
									{cell.feats === '_' ? '_' : cell.feats}
								</button>
							</td>
						{:else if col === 'misc'}
							<td class="border-r border-border px-1 py-0.5 {changed ? 'bg-blue-50 dark:bg-blue-950/30' : ''} {errors ? 'border-b-2 border-b-destructive' : ''}" title={errors ? errors.join('; ') : undefined}>
								<button
									onclick={() => openFeatsEditor(cell.id_f, cell.misc, 'misc')}
									class="w-full text-left rounded px-1 py-0.5 text-xs outline-none hover:bg-muted cursor-pointer truncate max-w-[10rem]"
									title={cell.misc}
								>
									{cell.misc === '_' ? '_' : cell.misc}
								</button>
							</td>
						{:else if isEditable(col)}
							<AnnotationCell
								value={cell[col]}
								field={col}
								tokenId={cell.id_f}
								onchange={handleCellChange}
								hasError={!!errors}
								errorMessages={errors ?? []}
								isChanged={changed}
							/>
						{:else}
							<td class="border-r border-border px-2 py-0.5 text-xs">{cell[col as keyof typeof cell]}</td>
						{/if}
					{/each}
					<td class="px-1 py-0.5">
						<div class="flex gap-1">
							<button
								onclick={() => addRow(cell.id_f)}
								class="rounded px-1 text-xs text-muted-foreground hover:text-foreground cursor-pointer"
								title="Add row after"
							>+</button>
							{#if !isMultiword}
								<button
									onclick={() => removeRow(cell.id_f)}
									class="rounded px-1 text-xs text-muted-foreground hover:text-destructive cursor-pointer"
									title="Remove row"
								>&times;</button>
							{/if}
						</div>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	.annotation-table-scroll {
		max-height: 70vh;
		overflow-y: auto;
	}
</style>

<!-- FEATS/MISC Editor Modal -->
{#if featsEditToken}
	<FeatsEditor
		value={featsEditValue}
		field={featsEditField}
		allowedFeatures={validationProfile?.allowed_features ?? null}
		allowedMisc={validationProfile?.allowed_misc ?? null}
		featureOrder={validationProfile?.feature_order ?? null}
		onchange={handleFeatsApply}
		onclose={() => (featsEditToken = null)}
	/>
{/if}
