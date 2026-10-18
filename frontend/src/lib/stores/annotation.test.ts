import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import {
	cells,
	initialCells,
	editHistory,
	redoStack,
	isDirty,
	canUndo,
	canRedo,
	updateCell,
	undo,
	redo,
	resetToInitial,
	type Cell,
	type CellField
} from './annotation';

function makeCell(id: string, form = '_'): Cell {
	return {
		id_f: id,
		form,
		lemma: '_',
		upos: '_',
		xpos: '_',
		feats: '_',
		head: '_',
		deprel: '_',
		deps: '_',
		misc: '_'
	};
}

function setupCells(list: Cell[]) {
	cells.set(list);
	initialCells.set(structuredClone(list));
	editHistory.set([]);
	redoStack.set([]);
}

describe('annotation store', () => {
	beforeEach(() => {
		setupCells([makeCell('1', 'Hello'), makeCell('2', 'world')]);
	});

	describe('updateCell', () => {
		it('updates the correct cell field', () => {
			updateCell('1', 'lemma', 'hello');
			const result = get(cells);
			expect(result[0].lemma).toBe('hello');
			expect(result[1].lemma).toBe('_');
		});

		it('does not modify cells if tokenId is not found', () => {
			const before = get(cells);
			updateCell('999', 'lemma', 'test');
			const after = get(cells);
			expect(after).toEqual(before);
		});

		it('does not record an edit if value is unchanged', () => {
			updateCell('1', 'form', 'Hello');
			expect(get(editHistory)).toHaveLength(0);
		});

		it('records an edit in history', () => {
			updateCell('1', 'form', 'Hi');
			const history = get(editHistory);
			expect(history).toHaveLength(1);
			expect(history[0]).toEqual({
				tokenId: '1',
				field: 'form',
				oldValue: 'Hello',
				newValue: 'Hi'
			});
		});

		it('clears redo stack on new edit', () => {
			updateCell('1', 'form', 'Hi');
			undo();
			expect(get(redoStack)).toHaveLength(1);
			updateCell('1', 'form', 'Hey');
			expect(get(redoStack)).toHaveLength(0);
		});
	});

	describe('undo', () => {
		it('restores the previous value', () => {
			updateCell('1', 'form', 'Hi');
			expect(get(cells)[0].form).toBe('Hi');
			undo();
			expect(get(cells)[0].form).toBe('Hello');
		});

		it('moves edit to redo stack', () => {
			updateCell('1', 'form', 'Hi');
			undo();
			expect(get(editHistory)).toHaveLength(0);
			expect(get(redoStack)).toHaveLength(1);
		});

		it('does nothing when history is empty', () => {
			const before = get(cells);
			undo();
			expect(get(cells)).toEqual(before);
		});
	});

	describe('redo', () => {
		it('reapplies the undone edit', () => {
			updateCell('1', 'form', 'Hi');
			undo();
			expect(get(cells)[0].form).toBe('Hello');
			redo();
			expect(get(cells)[0].form).toBe('Hi');
		});

		it('moves edit back to history', () => {
			updateCell('1', 'form', 'Hi');
			undo();
			redo();
			expect(get(editHistory)).toHaveLength(1);
			expect(get(redoStack)).toHaveLength(0);
		});

		it('does nothing when redo stack is empty', () => {
			const before = get(cells);
			redo();
			expect(get(cells)).toEqual(before);
		});
	});

	describe('edit history cap', () => {
		it('caps history at MAX_HISTORY (100)', () => {
			for (let i = 0; i < 110; i++) {
				updateCell('1', 'lemma', `val-${i}`);
			}
			expect(get(editHistory)).toHaveLength(100);
			// The oldest entries should have been dropped
			expect(get(editHistory)[0].newValue).toBe('val-10');
		});
	});

	describe('isDirty', () => {
		it('is false when cells match initial state', () => {
			expect(get(isDirty)).toBe(false);
		});

		it('is true after an edit', () => {
			updateCell('1', 'form', 'Changed');
			expect(get(isDirty)).toBe(true);
		});

		it('is false after undo restores original state', () => {
			updateCell('1', 'form', 'Changed');
			undo();
			expect(get(isDirty)).toBe(false);
		});

		it('is false after resetToInitial', () => {
			updateCell('1', 'form', 'Changed');
			resetToInitial();
			expect(get(isDirty)).toBe(false);
		});
	});

	describe('canUndo / canRedo', () => {
		it('canUndo is false initially', () => {
			expect(get(canUndo)).toBe(false);
		});

		it('canUndo is true after an edit', () => {
			updateCell('1', 'form', 'Hi');
			expect(get(canUndo)).toBe(true);
		});

		it('canRedo is false initially', () => {
			expect(get(canRedo)).toBe(false);
		});

		it('canRedo is true after undo', () => {
			updateCell('1', 'form', 'Hi');
			undo();
			expect(get(canRedo)).toBe(true);
		});
	});
});
