import { writable, derived, get } from 'svelte/store';
import type { WordLineRead, AnnotationDetail } from '$api/types';

export interface Cell {
	id_f: string;
	form: string;
	lemma: string;
	upos: string;
	xpos: string;
	feats: string;
	head: string;
	deprel: string;
	deps: string;
	misc: string;
}

export type CellField = keyof Omit<Cell, 'id_f'>;

export const CELL_FIELDS: CellField[] = [
	'form', 'lemma', 'upos', 'xpos', 'feats', 'head', 'deprel', 'deps', 'misc'
];

export const COLUMN_LABELS: Record<string, string> = {
	id_f: 'ID',
	form: 'FORM',
	lemma: 'LEMMA',
	upos: 'UPOS',
	xpos: 'XPOS',
	feats: 'FEATS',
	head: 'HEAD',
	deprel: 'DEPREL',
	deps: 'DEPS',
	misc: 'MISC'
};

const MAX_HISTORY = 100;

interface Edit {
	tokenId: string;
	field: CellField;
	oldValue: string;
	newValue: string;
}

// Core state
export const cells = writable<Cell[]>([]);
export const initialCells = writable<Cell[]>([]);
export const annotationId = writable<number | null>(null);
export const sentenceId = writable<number | null>(null);
export const sentId = writable('');
export const sentenceText = writable('');
export const sentenceMetadata = writable<Record<string, string> | null>(null);
export const status = writable(0);
export const notes = writable('');
export const isGold = writable(false);
export const isSaving = writable(false);
export const treebankCreatedBy = writable<number | null>(null);
export const annotatorId = writable<number | null>(null);

// Edit history
export const editHistory = writable<Edit[]>([]);
export const redoStack = writable<Edit[]>([]);

// Derived state
export const isDirty = derived([cells, initialCells], ([$cells, $initial]) => {
	if ($cells.length !== $initial.length) return true;
	return $cells.some((cell, i) => {
		const init = $initial[i];
		return CELL_FIELDS.some((f) => cell[f] !== init[f]);
	});
});

export const canUndo = derived(editHistory, ($h) => $h.length > 0);
export const canRedo = derived(redoStack, ($r) => $r.length > 0);

// Actions
export function loadAnnotation(detail: AnnotationDetail) {
	const wordlines = detail.wordlines.map(wordlineToCell);
	cells.set(wordlines);
	initialCells.set(structuredClone(wordlines));
	annotationId.set(detail.id);
	sentenceId.set(detail.sentence_id);
	sentId.set(detail.sentence_sent_id ?? '');
	sentenceText.set(detail.sentence_text ?? '');
	sentenceMetadata.set(detail.sentence_metadata);
	status.set(detail.status);
	notes.set(detail.notes ?? '');
	isGold.set(detail.is_gold);
	treebankCreatedBy.set(detail.treebank_created_by ?? null);
	annotatorId.set(detail.annotator_id);
	editHistory.set([]);
	redoStack.set([]);
	isSaving.set(false);
}

export function updateCell(tokenId: string, field: CellField, value: string) {
	cells.update(($cells) => {
		const idx = $cells.findIndex((c) => c.id_f === tokenId);
		if (idx === -1) return $cells;
		const oldValue = $cells[idx][field];
		if (oldValue === value) return $cells;

		editHistory.update(($h) => {
			const next = [...$h, { tokenId, field, oldValue, newValue: value }];
			return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
		});
		redoStack.set([]);

		const updated = [...$cells];
		updated[idx] = { ...updated[idx], [field]: value };
		return updated;
	});
}

export function undo() {
	const history = get(editHistory);
	if (history.length === 0) return;
	const last = history[history.length - 1];
	editHistory.set(history.slice(0, -1));
	redoStack.update(($r) => [...$r, last]);

	cells.update(($cells) => {
		const idx = $cells.findIndex((c) => c.id_f === last.tokenId);
		if (idx === -1) return $cells;
		const updated = [...$cells];
		updated[idx] = { ...updated[idx], [last.field]: last.oldValue };
		return updated;
	});
}

export function redo() {
	const stack = get(redoStack);
	if (stack.length === 0) return;
	const next = stack[stack.length - 1];
	redoStack.set(stack.slice(0, -1));
	editHistory.update(($h) => [...$h, next]);

	cells.update(($cells) => {
		const idx = $cells.findIndex((c) => c.id_f === next.tokenId);
		if (idx === -1) return $cells;
		const updated = [...$cells];
		updated[idx] = { ...updated[idx], [next.field]: next.newValue };
		return updated;
	});
}

export function resetToInitial() {
	const init = get(initialCells);
	cells.set(structuredClone(init));
	editHistory.set([]);
	redoStack.set([]);
}

export function addRow(afterId: string) {
	cells.update(($cells) => {
		const idx = $cells.findIndex((c) => c.id_f === afterId);
		if (idx === -1) return $cells;
		const newId = `${idx + 2}`;
		const newCell: Cell = {
			id_f: newId,
			form: '_',
			lemma: '_',
			upos: '_',
			xpos: '_',
			feats: '_',
			head: '_',
			deprel: '_',
			deps: '_',
			misc: '_'
		};
		const updated = [...$cells];
		updated.splice(idx + 1, 0, newCell);
		// Renumber
		return renumberCells(updated);
	});
}

export function removeRow(tokenId: string) {
	cells.update(($cells) => {
		const updated = $cells.filter((c) => c.id_f !== tokenId);
		return renumberCells(updated);
	});
}

function renumberCells(cells: Cell[]): Cell[] {
	let counter = 1;
	return cells.map((c) => {
		// Preserve multiword token IDs (e.g., "1-2") and empty nodes (e.g., "1.1")
		if (c.id_f.includes('-') || c.id_f.includes('.')) {
			return c;
		}
		return { ...c, id_f: String(counter++) };
	});
}

export function getCellsForSave(): Array<{
	id_f: string;
	form: string;
	lemma: string;
	upos: string;
	xpos: string;
	feats: string;
	head: string;
	deprel: string;
	deps: string;
	misc: string;
}> {
	return get(cells).map((c) => ({
		id_f: c.id_f,
		form: c.form,
		lemma: c.lemma,
		upos: c.upos,
		xpos: c.xpos,
		feats: c.feats,
		head: c.head,
		deprel: c.deprel,
		deps: c.deps,
		misc: c.misc
	}));
}

// Draft persistence (localStorage)
const DRAFT_PREFIX = 'boat-draft-';

export function saveDraft(id: number): void {
	try {
		const data = JSON.stringify(get(cells));
		localStorage.setItem(`${DRAFT_PREFIX}${id}`, data);
	} catch {
		// Ignore quota or serialization errors
	}
}

export function loadDraft(id: number): Cell[] | null {
	try {
		const raw = localStorage.getItem(`${DRAFT_PREFIX}${id}`);
		if (!raw) return null;
		return JSON.parse(raw) as Cell[];
	} catch {
		clearDraft(id);
		return null;
	}
}

export function clearDraft(id: number): void {
	try {
		localStorage.removeItem(`${DRAFT_PREFIX}${id}`);
	} catch {
		// Ignore
	}
}

function wordlineToCell(wl: WordLineRead): Cell {
	return {
		id_f: wl.id_f,
		form: wl.form,
		lemma: wl.lemma,
		upos: wl.upos,
		xpos: wl.xpos,
		feats: wl.feats,
		head: wl.head,
		deprel: wl.deprel,
		deps: wl.deps,
		misc: wl.misc
	};
}
