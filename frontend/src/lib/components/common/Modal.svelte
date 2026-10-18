<script lang="ts">
	import { onMount } from 'svelte';

	interface Props {
		open: boolean;
		title: string;
		onclose: () => void;
		children?: import('svelte').Snippet;
		actions?: import('svelte').Snippet;
		'aria-label'?: string;
	}

	let { open = $bindable(), title, onclose, children, actions, 'aria-label': ariaLabel }: Props = $props();

	let dialogEl: HTMLElement | undefined = $state();
	let previouslyFocused: HTMLElement | null = null;

	const focusableSelector = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]), [contenteditable="true"]';

	function getFocusableElements(): HTMLElement[] {
		if (!dialogEl) return [];
		return Array.from(dialogEl.querySelectorAll<HTMLElement>(focusableSelector));
	}

	$effect(() => {
		if (open) {
			previouslyFocused = document.activeElement as HTMLElement | null;
			// Defer focus to next tick so the DOM is rendered
			requestAnimationFrame(() => {
				const focusable = getFocusableElements();
				if (focusable.length > 0) {
					focusable[0].focus();
				} else {
					dialogEl?.focus();
				}
			});
		}
		return () => {
			if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
				previouslyFocused.focus();
				previouslyFocused = null;
			}
		};
	});

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onclose();
			return;
		}
		if (e.key === 'Tab') {
			const focusable = getFocusableElements();
			if (focusable.length === 0) {
				e.preventDefault();
				return;
			}
			const first = focusable[0];
			const last = focusable[focusable.length - 1];
			if (e.shiftKey) {
				if (document.activeElement === first) {
					e.preventDefault();
					last.focus();
				}
			} else {
				if (document.activeElement === last) {
					e.preventDefault();
					first.focus();
				}
			}
		}
	}

	function handleBackdrop() {
		onclose();
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		bind:this={dialogEl}
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
		role="dialog"
		aria-modal="true"
		aria-label={ariaLabel ?? title}
		tabindex="-1"
		onkeydown={handleKeydown}
		onclick={handleBackdrop}
	>
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="w-full max-w-lg rounded-lg bg-background p-6 shadow-lg"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<div class="mb-4 flex items-center justify-between">
				<h2 class="text-lg font-semibold">{title}</h2>
				<button class="text-muted-foreground hover:text-foreground cursor-pointer" onclick={onclose}>&times;</button>
			</div>
			<div class="mb-4">
				{@render children?.()}
			</div>
			{#if actions}
				<div class="flex justify-end gap-2">
					{@render actions()}
				</div>
			{/if}
		</div>
	</div>
{/if}
