<script lang="ts">
	import { toasts, toast as toastActions, type Toast } from '$stores/toast';

	const variantClasses: Record<Toast['variant'], string> = {
		success: 'border-success/30 bg-success/10 text-success',
		error: 'border-destructive/30 bg-destructive/10 text-destructive',
		info: 'border-primary/30 bg-primary/10 text-primary',
	};
</script>

<div class="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
	{#each $toasts as t (t.id)}
		<div
			class="toast-in flex items-center gap-3 rounded-lg border px-4 py-3 text-sm shadow-lg backdrop-blur-sm {variantClasses[t.variant]}"
		>
			<span class="flex-1">{t.message}</span>
			<button
				onclick={() => toastActions.dismiss(t.id)}
				class="opacity-60 hover:opacity-100 cursor-pointer text-current"
			>&times;</button>
		</div>
	{/each}
</div>
