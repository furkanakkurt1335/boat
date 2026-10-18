<script lang="ts">
	import { cn } from '$utils/cn';

	interface Props {
		type?: string;
		value?: string;
		placeholder?: string;
		required?: boolean;
		disabled?: boolean;
		id?: string;
		name?: string;
		class?: string;
		oninput?: (e: Event) => void;
		'aria-invalid'?: boolean;
		'aria-describedby'?: string;
	}

	let {
		type = 'text',
		value = $bindable(''),
		placeholder = '',
		required = false,
		disabled = false,
		id,
		name,
		class: className = '',
		oninput,
		'aria-invalid': ariaInvalid,
		'aria-describedby': ariaDescribedby
	}: Props = $props();
</script>

<input
	{type}
	{placeholder}
	{required}
	{disabled}
	{id}
	{name}
	{oninput}
	aria-invalid={ariaInvalid}
	aria-describedby={ariaDescribedby}
	bind:value
	class={cn(
		'flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50',
		className
	)}
/>
