<script lang="ts">
	import { getStatusConfig } from '$utils/status';

	interface Props {
		status: number;
	}

	let { status }: Props = $props();

	const config = $derived(getStatusConfig(status));
</script>

<span class="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium {config.color}">
	<span class="h-1.5 w-1.5 rounded-full {config.dot}"></span>
	{config.label}
</span>
