<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		icon?: any;
		title: string;
		description?: string;
		children?: Snippet;
	}

	let { icon: Icon, title, description, children }: Props = $props();
</script>

<div class="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-12 text-center">
	{#if Icon}
		<div class="mb-3 text-muted-foreground">
			<Icon class="h-10 w-10 stroke-[1.5]" />
		</div>
	{/if}
	<p class="text-sm font-medium text-foreground">{title}</p>
	{#if description}
		<p class="mt-1 text-sm text-muted-foreground">{description}</p>
	{/if}
	{#if children}
		<div class="mt-3">
			{@render children()}
		</div>
	{/if}
</div>
