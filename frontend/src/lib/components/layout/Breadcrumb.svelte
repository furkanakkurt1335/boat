<script lang="ts">
	import { ChevronRight } from 'lucide-svelte';

	interface Crumb {
		label: string;
		href?: string;
	}

	interface Props {
		crumbs: Crumb[];
	}

	let { crumbs }: Props = $props();
</script>

<nav class="flex items-center gap-1 text-sm text-muted-foreground">
	{#each crumbs as crumb, i}
		{#if i > 0}
			<ChevronRight class="h-3.5 w-3.5 shrink-0" />
		{/if}
		{#if crumb.href && i < crumbs.length - 1}
			<a href={crumb.href} class="hover:text-foreground transition-colors">{crumb.label}</a>
		{:else}
			<span class="text-foreground font-medium truncate">{crumb.label}</span>
		{/if}
	{/each}
</nav>
