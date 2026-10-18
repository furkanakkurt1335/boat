import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createShortcutManager, type Shortcut } from './keyboard';

function makeKeyEvent(
	key: string,
	opts: { ctrl?: boolean; alt?: boolean; shift?: boolean; target?: Partial<HTMLElement> } = {}
): KeyboardEvent {
	const event = new KeyboardEvent('keydown', {
		key,
		ctrlKey: opts.ctrl ?? false,
		altKey: opts.alt ?? false,
		shiftKey: opts.shift ?? false,
		bubbles: true
	});
	if (opts.target) {
		Object.defineProperty(event, 'target', { value: opts.target });
	}
	return event;
}

describe('createShortcutManager', () => {
	let manager: ReturnType<typeof createShortcutManager>;

	beforeEach(() => {
		manager = createShortcutManager();
		manager.attach();
	});

	afterEach(() => {
		manager.detach();
	});

	it('calls handler when shortcut key matches', () => {
		const handler = vi.fn();
		manager.register([{ key: 's', ctrl: true, handler, description: 'Save' }]);

		window.dispatchEvent(makeKeyEvent('s', { ctrl: true }));
		expect(handler).toHaveBeenCalledOnce();
	});

	it('does not call handler when modifier does not match', () => {
		const handler = vi.fn();
		manager.register([{ key: 's', ctrl: true, handler, description: 'Save' }]);

		// No ctrl pressed
		window.dispatchEvent(makeKeyEvent('s'));
		expect(handler).not.toHaveBeenCalled();
	});

	it('matches case-insensitively', () => {
		const handler = vi.fn();
		manager.register([{ key: 'a', handler, description: 'Action' }]);

		window.dispatchEvent(makeKeyEvent('A'));
		expect(handler).toHaveBeenCalledOnce();
	});

	it('handles alt modifier', () => {
		const handler = vi.fn();
		manager.register([{ key: 'n', alt: true, handler, description: 'Next' }]);

		window.dispatchEvent(makeKeyEvent('n', { alt: true }));
		expect(handler).toHaveBeenCalledOnce();
	});

	it('handles shift modifier', () => {
		const handler = vi.fn();
		manager.register([{ key: 'z', ctrl: true, shift: true, handler, description: 'Redo' }]);

		window.dispatchEvent(makeKeyEvent('z', { ctrl: true, shift: true }));
		expect(handler).toHaveBeenCalledOnce();
	});

	it('does not trigger when extra modifier is pressed', () => {
		const handler = vi.fn();
		manager.register([{ key: 'a', handler, description: 'Action' }]);

		window.dispatchEvent(makeKeyEvent('a', { ctrl: true }));
		expect(handler).not.toHaveBeenCalled();
	});

	it('ignores shortcuts when target is an INPUT', () => {
		const handler = vi.fn();
		manager.register([{ key: 'a', handler, description: 'Action' }]);

		window.dispatchEvent(makeKeyEvent('a', { target: { tagName: 'INPUT' } }));
		expect(handler).not.toHaveBeenCalled();
	});

	it('ignores shortcuts when target is a TEXTAREA', () => {
		const handler = vi.fn();
		manager.register([{ key: 'a', handler, description: 'Action' }]);

		window.dispatchEvent(makeKeyEvent('a', { target: { tagName: 'TEXTAREA' } }));
		expect(handler).not.toHaveBeenCalled();
	});

	it('allows Ctrl+Z in contenteditable elements', () => {
		const undoHandler = vi.fn();
		manager.register([{ key: 'z', ctrl: true, handler: undoHandler, description: 'Undo' }]);

		window.dispatchEvent(
			makeKeyEvent('z', {
				ctrl: true,
				target: { tagName: 'DIV', isContentEditable: true }
			})
		);
		expect(undoHandler).toHaveBeenCalledOnce();
	});

	it('blocks non-undo shortcuts in contenteditable elements', () => {
		const handler = vi.fn();
		manager.register([{ key: 'a', handler, description: 'Action' }]);

		window.dispatchEvent(
			makeKeyEvent('a', {
				target: { tagName: 'DIV', isContentEditable: true }
			})
		);
		expect(handler).not.toHaveBeenCalled();
	});

	it('stops listening after detach', () => {
		const handler = vi.fn();
		manager.register([{ key: 'a', handler, description: 'Action' }]);
		manager.detach();

		window.dispatchEvent(makeKeyEvent('a'));
		expect(handler).not.toHaveBeenCalled();
	});

	it('returns registered shortcuts via getShortcuts', () => {
		const shortcuts: Shortcut[] = [
			{ key: 'a', handler: vi.fn(), description: 'A' },
			{ key: 'b', ctrl: true, handler: vi.fn(), description: 'B' }
		];
		manager.register(shortcuts);
		expect(manager.getShortcuts()).toEqual(shortcuts);
	});
});
