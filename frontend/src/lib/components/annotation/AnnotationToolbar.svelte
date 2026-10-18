<script lang="ts">
	import { status, isDirty, canUndo, canRedo, isSaving, undo, redo, resetToInitial, notes, treebankCreatedBy, annotatorId } from '$stores/annotation';
	import { user } from '$stores/auth';
	import { AnnotationStatus } from '$api/types';
	import StatusBadge from '$components/common/StatusBadge.svelte';
	import Button from '$components/common/Button.svelte';
	import Tooltip from '$components/common/Tooltip.svelte';

	interface Props {
		visibleColumns: string[];
		oncolumnschange: (cols: string[]) => void;
		onsave: () => void;
		onstatuschange: (newStatus: number) => void;
		onnext: () => void;
		onprev: () => void;
		hasPrev: boolean;
		hasNext: boolean;
		loading?: boolean;
	}

	let { visibleColumns = $bindable(), oncolumnschange, onsave, onstatuschange, onnext, onprev, hasPrev, hasNext, loading = false }: Props = $props();

	const allColumns = ['ID', 'FORM', 'LEMMA', 'UPOS', 'XPOS', 'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC'];

	let showNotes = $state(false);

	const isOwner = $derived($user?.id === $annotatorId);
	const isReviewer = $derived($user?.id === $treebankCreatedBy);

	// Annotator workflow buttons
	const canSubmit = $derived(isOwner && $status === AnnotationStatus.DRAFT);
	const canRevise = $derived(isOwner && $status === AnnotationStatus.REJECTED);

	// Reviewer workflow buttons
	const canApproveReject = $derived(isReviewer && $status === AnnotationStatus.SUBMITTED);

	function toggleColumn(col: string) {
		if (col === 'ID' || col === 'FORM') return; // Always visible
		const next = visibleColumns.includes(col)
			? visibleColumns.filter((c) => c !== col)
			: [...visibleColumns, col];
		oncolumnschange(next);
	}
</script>

<div class="flex flex-col gap-2 rounded-lg border border-border bg-background p-3">
	<!-- Top row: navigation + save -->
	<div class="flex items-center justify-between gap-2">
		<div class="flex items-center gap-2">
			<Tooltip text="Previous sentence (Alt+P)">
				<Button variant="outline" size="sm" onclick={onprev} disabled={!hasPrev || loading}>
					Prev
				</Button>
			</Tooltip>
			<Tooltip text="Next sentence (Alt+N)">
				<Button variant="outline" size="sm" onclick={onnext} disabled={!hasNext || loading}>
					Next
				</Button>
			</Tooltip>
		</div>

		<div class="flex items-center gap-2">
			<Tooltip text="Undo (Ctrl+Z)">
				<Button variant="ghost" size="sm" onclick={undo} disabled={!$canUndo}>
					Undo
				</Button>
			</Tooltip>
			<Tooltip text="Redo (Ctrl+Y)">
				<Button variant="ghost" size="sm" onclick={redo} disabled={!$canRedo}>
					Redo
				</Button>
			</Tooltip>
			<Button variant="ghost" size="sm" onclick={resetToInitial} disabled={!$isDirty}>
				Reset
			</Button>
		</div>

		<div class="flex items-center gap-3">
			<StatusBadge status={$status} />

			<!-- Workflow buttons -->
			{#if canSubmit}
				<Tooltip text="Submit annotation for review">
					<Button
						variant="outline"
						size="sm"
						onclick={() => onstatuschange(AnnotationStatus.SUBMITTED)}
						disabled={$isSaving || $isDirty}
					>
						Submit for Review
					</Button>
				</Tooltip>
			{/if}

			{#if canRevise}
				<Tooltip text="Revise rejected annotation">
					<Button
						variant="outline"
						size="sm"
						onclick={() => onstatuschange(AnnotationStatus.DRAFT)}
						disabled={$isSaving}
					>
						Revise
					</Button>
				</Tooltip>
			{/if}

			{#if canApproveReject}
				<Tooltip text="Approve this annotation">
					<Button
						variant="outline"
						size="sm"
						onclick={() => onstatuschange(AnnotationStatus.APPROVED)}
						disabled={$isSaving}
						class="border-success/50 text-success hover:bg-success/10"
					>
						Approve
					</Button>
				</Tooltip>
				<Tooltip text="Reject this annotation">
					<Button
						variant="outline"
						size="sm"
						onclick={() => onstatuschange(AnnotationStatus.REJECTED)}
						disabled={$isSaving}
						class="border-destructive/50 text-destructive hover:bg-destructive/10"
					>
						Reject
					</Button>
				</Tooltip>
			{/if}

			<Tooltip text="Save annotation (Alt+S)">
				<Button
					size="sm"
					onclick={onsave}
					disabled={$isSaving}
				>
					{$isSaving ? 'Saving...' : $isDirty ? 'Save *' : 'Save'}
				</Button>
			</Tooltip>
		</div>
	</div>

	<!-- Column toggles + notes -->
	<div class="flex items-center justify-between gap-2">
		<div class="flex flex-wrap gap-1">
			{#each allColumns as col}
				{@const active = visibleColumns.includes(col)}
				{@const locked = col === 'ID' || col === 'FORM'}
				<button
					onclick={() => toggleColumn(col)}
					disabled={locked}
					class="rounded-full px-2 py-0.5 text-xs font-medium transition-colors cursor-pointer
						{active ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}
						{locked ? 'opacity-60 cursor-default' : 'hover:opacity-80'}"
				>
					{col}
				</button>
			{/each}
		</div>
		<button
			onclick={() => (showNotes = !showNotes)}
			class="text-xs text-muted-foreground hover:text-foreground cursor-pointer"
		>
			{showNotes ? 'Hide notes' : 'Notes'}
		</button>
	</div>

	<!-- Notes area (collapsible) -->
	{#if showNotes}
		<textarea
			bind:value={$notes}
			rows="2"
			placeholder="Annotator notes..."
			class="w-full rounded-md border border-input bg-background px-3 py-2 text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
		></textarea>
	{/if}
</div>
