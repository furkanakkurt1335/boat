<script lang="ts">
	import { AlertTriangle } from 'lucide-svelte';
	import Button from '$components/common/Button.svelte';

	interface Props {
		message: string;
		onRetry?: () => void;
	}

	let { message, onRetry }: Props = $props();
</script>

<div class="flex flex-col items-center justify-center rounded-lg border border-dashed border-destructive/40 bg-destructive/5 py-12 text-center">
	<div class="mb-3 text-destructive">
		<AlertTriangle class="h-10 w-10 stroke-[1.5]" />
	</div>
	<p class="text-sm font-medium text-foreground">{message}</p>
	{#if onRetry}
		<div class="mt-3">
			<Button variant="outline" size="sm" onclick={onRetry}>Try Again</Button>
		</div>
	{/if}
</div>
