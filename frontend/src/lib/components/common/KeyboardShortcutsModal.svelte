<script lang="ts">
	import type { Shortcut } from '$utils/keyboard';
	import Modal from './Modal.svelte';

	interface Props {
		open: boolean;
		shortcuts: Shortcut[];
		onclose: () => void;
	}

	let { open, shortcuts, onclose }: Props = $props();

	function formatKey(s: Shortcut): string {
		const parts: string[] = [];
		if (s.ctrl) parts.push('Ctrl');
		if (s.alt) parts.push('Alt');
		if (s.shift) parts.push('Shift');
		parts.push(s.key.length === 1 ? s.key.toUpperCase() : s.key);
		return parts.join(' + ');
	}

	// Group shortcuts by category
	const grouped = $derived(() => {
		const nav: Shortcut[] = [];
		const edit: Shortcut[] = [];
		const view: Shortcut[] = [];

		for (const s of shortcuts) {
			const desc = s.description.toLowerCase();
			if (desc.includes('previous') || desc.includes('next') || desc.includes('exit')) {
				nav.push(s);
			} else if (desc.includes('undo') || desc.includes('redo') || desc.includes('save') || desc.includes('head')) {
				edit.push(s);
			} else {
				view.push(s);
			}
		}
		return { Navigation: nav, Editing: edit, View: view };
	});
</script>

<Modal {open} title="Keyboard Shortcuts" {onclose}>
	<div class="space-y-4">
		{#each Object.entries(grouped()) as [category, items]}
			{#if items.length > 0}
				<div>
					<h3 class="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">{category}</h3>
					<div class="space-y-1.5">
						{#each items as shortcut}
							<div class="flex items-center justify-between text-sm">
								<span>{shortcut.description}</span>
								<kbd class="rounded border border-border bg-muted px-2 py-0.5 font-mono text-xs text-muted-foreground">
									{formatKey(shortcut)}
								</kbd>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		{/each}
	</div>
</Modal>
