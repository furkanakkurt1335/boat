import type { Cell } from '$stores/annotation';

export interface ValidationError {
	key: string; // `${id_f}:${field}`
	messages: string[];
}

/**
 * Check that exactly one token has HEAD=0 (root).
 * Returns errors keyed to the HEAD field of offending tokens.
 */
function validateSingleRoot(cells: Cell[]): Map<string, string[]> {
	const errors = new Map<string, string[]>();
	const regularCells = cells.filter((c) => !c.id_f.includes('-') && !c.id_f.includes('.'));
	const roots = regularCells.filter((c) => c.head === '0');

	if (roots.length === 0) {
		// Mark the first regular token's HEAD as having no root
		if (regularCells.length > 0) {
			const key = `${regularCells[0].id_f}:head`;
			pushError(errors, key, 'No root found: exactly one token must have HEAD=0');
		}
	} else if (roots.length > 1) {
		for (const root of roots) {
			const key = `${root.id_f}:head`;
			pushError(errors, key, `Multiple roots: ${roots.length} tokens have HEAD=0`);
		}
	}

	return errors;
}

/**
 * HEAD value must be 0 or a valid token ID. No self-loops.
 */
function validateHeadRange(cells: Cell[]): Map<string, string[]> {
	const errors = new Map<string, string[]>();
	const validIds = new Set(cells.map((c) => c.id_f));

	for (const cell of cells) {
		if (cell.id_f.includes('-') || cell.id_f.includes('.')) continue;
		if (cell.head === '_' || cell.head === '') continue;

		const key = `${cell.id_f}:head`;

		if (cell.head === cell.id_f) {
			pushError(errors, key, 'Self-loop: HEAD equals own ID');
			continue;
		}

		if (cell.head !== '0') {
			const n = parseInt(cell.head);
			if (isNaN(n) || n < 0) {
				pushError(errors, key, `Invalid HEAD value: ${cell.head}`);
			} else if (!validIds.has(cell.head)) {
				pushError(errors, key, `HEAD ${cell.head} does not refer to an existing token`);
			}
		}
	}

	return errors;
}

/**
 * Detect cycles in the HEAD graph.
 */
function validateCycles(cells: Cell[]): Map<string, string[]> {
	const errors = new Map<string, string[]>();
	const regularCells = cells.filter((c) => !c.id_f.includes('-') && !c.id_f.includes('.'));

	// Build head map: token_id -> head_id
	const headMap = new Map<string, string>();
	for (const cell of regularCells) {
		if (cell.head && cell.head !== '_' && cell.head !== '') {
			headMap.set(cell.id_f, cell.head);
		}
	}

	// For each token, follow HEAD pointers and detect revisits
	const validIds = new Set(regularCells.map((c) => c.id_f));

	for (const cell of regularCells) {
		const visited = new Set<string>();
		let current = cell.id_f;

		while (current !== '0' && validIds.has(current)) {
			if (visited.has(current)) {
				// Cycle detected — mark all tokens in the cycle
				for (const id of visited) {
					const key = `${id}:head`;
					pushError(errors, key, 'Cycle detected in HEAD chain');
				}
				break;
			}
			visited.add(current);
			const head = headMap.get(current);
			if (!head || head === '_' || head === '') break;
			current = head;
		}
	}

	return errors;
}

/**
 * FORM and UPOS should not be empty for regular tokens.
 */
function validateRequiredFields(cells: Cell[]): Map<string, string[]> {
	const errors = new Map<string, string[]>();

	for (const cell of cells) {
		if (cell.id_f.includes('-')) continue; // skip multiword tokens

		if (!cell.form || cell.form.trim() === '') {
			pushError(errors, `${cell.id_f}:form`, 'FORM is required');
		}

		if (!cell.upos || cell.upos.trim() === '' || cell.upos === '_') {
			pushError(errors, `${cell.id_f}:upos`, 'UPOS is required');
		}
	}

	return errors;
}

/**
 * Run all validators and return a merged error map.
 */
export function validateAll(cells: Cell[]): Map<string, string[]> {
	const merged = new Map<string, string[]>();

	const validators = [
		validateSingleRoot,
		validateHeadRange,
		validateCycles,
		validateRequiredFields,
	];

	for (const validate of validators) {
		const result = validate(cells);
		for (const [key, messages] of result) {
			const existing = merged.get(key);
			if (existing) {
				// Deduplicate messages
				for (const msg of messages) {
					if (!existing.includes(msg)) {
						existing.push(msg);
					}
				}
			} else {
				merged.set(key, [...messages]);
			}
		}
	}

	return merged;
}

/**
 * Count total number of unique error keys.
 */
export function errorCount(errors: Map<string, string[]>): number {
	return errors.size;
}

function pushError(map: Map<string, string[]>, key: string, message: string) {
	const existing = map.get(key);
	if (existing) {
		if (!existing.includes(message)) {
			existing.push(message);
		}
	} else {
		map.set(key, [message]);
	}
}
