<script lang="ts">
	import type { CellField } from '$stores/annotation';

	interface Props {
		value: string;
		field: CellField;
		tokenId: string;
		onchange: (tokenId: string, field: CellField, value: string) => void;
		hasError?: boolean;
		errorMessages?: string[];
		isChanged?: boolean;
	}

	let { value, field, tokenId, onchange, hasError = false, errorMessages = [], isChanged = false }: Props = $props();

	let cellEl: HTMLElement | undefined = $state();

	function handleBlur() {
		if (!cellEl) return;
		const newValue = cellEl.textContent?.trim() ?? '';
		if (newValue !== value) {
			onchange(tokenId, field, newValue);
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			cellEl?.blur();
		}
		if (e.key === 'Tab') {
			e.preventDefault();
			cellEl?.blur();
			const td = cellEl?.parentElement;
			const next = e.shiftKey
				? td?.previousElementSibling?.querySelector<HTMLElement>('[contenteditable], input')
				: td?.nextElementSibling?.querySelector<HTMLElement>('[contenteditable], input');
			if (next) {
				next.focus();
			} else {
				// Wrap to next/previous row
				const row = td?.closest('tr');
				const targetRow = e.shiftKey ? row?.previousElementSibling : row?.nextElementSibling;
				if (targetRow) {
					const cells = targetRow.querySelectorAll<HTMLElement>('[contenteditable], input');
					const wrap = e.shiftKey ? cells[cells.length - 1] : cells[0];
					wrap?.focus();
				}
			}
		}
		if (e.key === 'Escape') {
			if (cellEl) cellEl.textContent = value;
			cellEl?.blur();
		}
		// Shift+Arrow navigation between rows
		if (e.shiftKey && !e.ctrlKey && !e.altKey) {
			if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
				e.preventDefault();
				cellEl?.blur();
				const row = cellEl?.closest('tr');
				const targetRow = e.key === 'ArrowDown' ? row?.nextElementSibling : row?.previousElementSibling;
				if (targetRow) {
					const cellIndex = Array.from(row?.children ?? []).indexOf(cellEl?.parentElement!);
					const targetCell = targetRow.children[cellIndex]?.querySelector<HTMLElement>('[contenteditable]');
					targetCell?.focus();
				}
			}
		}
	}

	function handlePaste(e: ClipboardEvent) {
		e.preventDefault();
		const text = e.clipboardData?.getData('text/plain') ?? '';
		const sel = window.getSelection();
		if (!sel || sel.rangeCount === 0) return;
		const range = sel.getRangeAt(0);
		range.deleteContents();
		range.insertNode(document.createTextNode(text));
		range.collapse(false);
	}

	function handleFocus() {
		// Select all text on focus
		if (cellEl) {
			const range = document.createRange();
			range.selectNodeContents(cellEl);
			const sel = window.getSelection();
			sel?.removeAllRanges();
			sel?.addRange(range);
		}
	}
</script>

<td
	class="border-r border-border px-1 py-0.5 {isChanged ? 'bg-blue-50 dark:bg-blue-950/30' : ''} {hasError ? 'border-b-2 border-b-destructive' : ''}"
	title={hasError ? errorMessages.join('; ') : undefined}
>
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		bind:this={cellEl}
		contenteditable="true"
		role="textbox"
		tabindex="0"
		aria-label="{field.toUpperCase()} for token {tokenId}"
		aria-invalid={hasError}
		class="min-w-[2.5rem] rounded px-1 py-0.5 text-xs outline-none focus:ring-2 focus:ring-ring focus:bg-background {hasError ? 'text-destructive' : ''}"
		onblur={handleBlur}
		onkeydown={handleKeydown}
		onfocus={handleFocus}
		onpaste={handlePaste}
	>
		{value}
	</div>
</td>
