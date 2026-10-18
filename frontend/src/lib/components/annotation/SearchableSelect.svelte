<script lang="ts">
	interface Props {
		value: string;
		options: readonly string[];
		onchange: (value: string) => void;
		class?: string;
		title?: string;
	}

	let { value, options, onchange, class: className = '', title: titleAttr = undefined }: Props = $props();

	let open = $state(false);
	let filter = $state('');
	let inputEl: HTMLInputElement | undefined = $state();
	let highlightIdx = $state(0);

	// Sync filter with external value changes when dropdown is closed
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
		// Delay to allow click on option
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
			e.preventDefault();
			if (filtered.length > 0) {
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

<td class="border-r border-border px-0.5 py-0.5 relative" title={titleAttr}>
	<input
		bind:this={inputEl}
		value={open ? filter : value}
		onfocus={handleFocus}
		onblur={handleBlur}
		oninput={handleInput}
		onkeydown={handleKeydown}
		class="w-full min-w-[3rem] rounded px-1 py-0.5 text-xs outline-none focus:ring-2 focus:ring-ring bg-transparent {className}"
	/>
	{#if open && filtered.length > 0}
		<div class="absolute left-0 top-full z-50 mt-0.5 max-h-40 w-max min-w-full overflow-auto rounded-md border border-border bg-background shadow-lg">
			{#each filtered as opt, i}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class="cursor-pointer px-2 py-1 text-xs {i === highlightIdx ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}"
					onmousedown={() => selectOption(opt)}
				>
					{opt}
				</div>
			{/each}
		</div>
	{/if}
</td>
