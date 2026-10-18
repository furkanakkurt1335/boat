export interface Shortcut {
	key: string;
	alt?: boolean;
	ctrl?: boolean;
	shift?: boolean;
	handler: () => void;
	description: string;
}

export function createShortcutManager() {
	let shortcuts: Shortcut[] = [];

	function handleKeydown(e: KeyboardEvent) {
		// Don't trigger shortcuts when typing in form fields
		const tag = (e.target as HTMLElement)?.tagName;
		const isEditable = (e.target as HTMLElement)?.isContentEditable;
		if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

		// In contenteditable cells, only allow Ctrl+Z/Y (undo/redo)
		if (isEditable) {
			if (e.ctrlKey && (e.key === 'z' || e.key === 'y')) {
				e.preventDefault();
				const undo = shortcuts.find((s) => s.ctrl && s.key === 'z');
				const redo = shortcuts.find((s) => s.ctrl && s.key === 'y');
				if (e.key === 'z' && undo) undo.handler();
				if (e.key === 'y' && redo) redo.handler();
			}
			return;
		}

		for (const s of shortcuts) {
			if (
				e.key.toLowerCase() === s.key.toLowerCase() &&
				!!e.altKey === !!s.alt &&
				!!e.ctrlKey === !!s.ctrl &&
				!!e.shiftKey === !!s.shift
			) {
				e.preventDefault();
				s.handler();
				return;
			}
		}
	}

	return {
		register(newShortcuts: Shortcut[]) {
			shortcuts = newShortcuts;
		},
		attach() {
			window.addEventListener('keydown', handleKeydown);
		},
		detach() {
			window.removeEventListener('keydown', handleKeydown);
		},
		getShortcuts(): Shortcut[] {
			return shortcuts;
		}
	};
}
