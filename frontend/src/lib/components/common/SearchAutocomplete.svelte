<script lang="ts">
	interface Props {
		value: string;
		options: readonly string[] | string[];
		onchange: (value: string) => void;
		placeholder?: string;
		class?: string;
	}

	let { value, options, onchange, placeholder = '', class: className = '' }: Props = $props();

	let open = $state(false);
	let filter = $state('');
	let inputEl: HTMLInputElement | undefined = $state();
	let highlightIdx = $state(0);

	$effect(() => {
		if (!open) filter = value;
	});

	const filtered = $derived(
		filter
			? options.filter((o) => o.toLowerCase().includes(filter.toLowerCase()))
			: [...options]
	);

	function handleFocus() {
		filter = '';
		open = true;
		highlightIdx = 0;
	}

	function handleBlur() {
		setTimeout(() => {
			open = false;
			filter = value;
		}, 150);
	}

	function handleInput(e: Event) {
		filter = (e.target as HTMLInputElement).value;
		open = true;
		highlightIdx = 0;
	}

	function selectOption(opt: string) {
		onchange(opt);
		filter = opt;
		open = false;
		inputEl?.blur();
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			highlightIdx = Math.min(highlightIdx + 1, filtered.length - 1);
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			highlightIdx = Math.max(highlightIdx - 1, 0);
		} else if (e.key === 'Enter') {
			if (open && filtered.length > 0) {
				e.preventDefault();
				selectOption(filtered[highlightIdx]);
			}
		} else if (e.key === 'Escape') {
			open = false;
			filter = value;
			inputEl?.blur();
		} else if (e.key === 'Tab') {
			if (filtered.length > 0 && open) {
				selectOption(filtered[highlightIdx]);
			}
		}
	}
</script>

<div class="relative {className}">
	<input
		bind:this={inputEl}
		value={open ? filter : value}
		onfocus={handleFocus}
		onblur={handleBlur}
		oninput={handleInput}
		onkeydown={handleKeydown}
		{placeholder}
		class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
	/>
	{#if open && filtered.length > 0}
		<div class="absolute left-0 top-full z-50 mt-1 max-h-48 w-full overflow-auto rounded-md border border-border bg-background shadow-lg">
			{#each filtered as opt, i}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class="cursor-pointer px-3 py-1.5 text-sm {i === highlightIdx ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}"
					onmousedown={() => selectOption(opt)}
				>
					{opt}
				</div>
			{/each}
		</div>
	{/if}
</div>
