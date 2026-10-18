<script lang="ts">
	interface Props {
		text: string;
		children: import('svelte').Snippet;
	}

	let { text, children }: Props = $props();
</script>

<span class="tooltip-wrapper relative inline-flex">
	{@render children()}
	<span
		class="tooltip-text pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-md border border-border bg-background px-2 py-1 text-xs text-foreground shadow-md opacity-0 transition-opacity"
	>{text}</span>
</span>

<style>
	.tooltip-wrapper:hover .tooltip-text {
		opacity: 1;
	}
</style>
