<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { getAnnotationByPosition, updateAnnotation, updateWordlines, cloneAnnotation } from '$api/annotations';
	import { listSentences, listSentenceAnnotations } from '$api/sentences';
	import { getTreebankByTitle } from '$api/treebanks';
	import { ApiError } from '$api/client';
	import {
		loadAnnotation,
		cells,
		annotationId,
		sentId,
		sentenceText,
		sentenceMetadata,
		notes,
		isDirty,
		isSaving,
		getCellsForSave,
		updateCell,
		saveDraft,
		loadDraft,
		clearDraft
	} from '$stores/annotation';
	import { currentColumns, graphPreference } from '$stores/preferences';
	import { appMode } from '$stores/mode';
	import { createShortcutManager } from '$utils/keyboard';
	import { undo, redo } from '$stores/annotation';
	import AnnotationTable from '$components/annotation/AnnotationTable.svelte';
	import AnnotationToolbar from '$components/annotation/AnnotationToolbar.svelte';
	import CommentsPanel from '$components/annotation/CommentsPanel.svelte';
	import DisplacyGraph from '$components/graph/DisplacyGraph.svelte';
	import Breadcrumb from '$components/layout/Breadcrumb.svelte';
	import Tooltip from '$components/common/Tooltip.svelte';
	import KeyboardShortcutsModal from '$components/common/KeyboardShortcutsModal.svelte';
	import ErrorState from '$components/common/ErrorState.svelte';
	import { toast } from '$stores/toast';
	import { user } from '$stores/auth';
	import type { TreebankRead, ValidationProfileRead, AnnotationRead } from '$api/types';
	import { getValidationProfile } from '$api/validation';
	import { validateAll, errorCount } from '$utils/validation';

	const treebankSlug = $derived(decodeURIComponent(page.params.treebank!));
	const order = $derived(Number(page.params.order!));
	const offline = $derived($appMode === 'offline');

	let treebank = $state<TreebankRead | null>(null);
	let validationProfile = $state<ValidationProfileRead | null>(null);
	let loading = $state(true);
	let error = $state('');
	let maxOrder = $state(0);
	let visibleColumns = $state<string[]>([]);
	let showComments = $state(false);
	let showGraph = $state(true);

	// Other users' annotations available for cloning
	let otherAnnotations = $state<AnnotationRead[]>([]);
	let cloning = $state(false);

	// Token count for auto-hiding graph on long sentences
	const tokenCount = $derived($cells.filter((c) => !c.id_f.includes('-') && !c.id_f.includes('.')).length);

	// Real-time validation errors (recomputes on every cell edit)
	const validationErrors = $derived(validateAll($cells));
	const validationErrorCount = $derived(errorCount(validationErrors));

	// Click-to-set-HEAD mode
	let selectedTokenId = $state<string | null>(null);
	let headSelectionMode = $state(false);
	let showShortcuts = $state(false);
	let showHints = $state(false);

	const shortcutManager = createShortcutManager();

	onMount(async () => {
		visibleColumns = $currentColumns;
		// Restore graph visibility from localStorage, falling back to user preference
		const storedGraphPref = localStorage.getItem('boat-show-graph');
		showGraph = storedGraphPref !== null ? storedGraphPref === '1' : $graphPreference !== 0;

		// First-use hints
		const dismissed = localStorage.getItem('boat-hints-dismissed');
		if (!dismissed) showHints = true;
		shortcutManager.register([
			{ key: 'p', alt: true, handler: goPrev, description: 'Previous sentence' },
			{ key: 'n', alt: true, handler: goNext, description: 'Next sentence' },
			{ key: 's', alt: true, handler: save, description: 'Save' },
			{ key: 'z', ctrl: true, handler: undo, description: 'Undo' },
			{ key: 'y', ctrl: true, handler: redo, description: 'Redo' },
			{ key: 'd', alt: true, handler: () => (showComments = !showComments), description: 'Toggle discussion' },
			{ key: 'g', alt: true, handler: toggleGraph, description: 'Toggle graph' },
			{ key: 'h', alt: true, handler: () => (headSelectionMode = !headSelectionMode), description: 'Toggle HEAD selection mode' },
			{ key: 'Escape', handler: () => { headSelectionMode = false; }, description: 'Exit HEAD selection mode' },
			{ key: '?', shift: true, handler: () => (showShortcuts = !showShortcuts), description: 'Show keyboard shortcuts' },
		]);
		shortcutManager.attach();

		// Listen for desktop save events (Ctrl+S from DesktopShortcuts)
		window.addEventListener('boat:save', save);
		window.addEventListener('boat:save-as', saveAs);

		await loadPage();
	});

	onDestroy(() => {
		shortcutManager.detach();
		window.removeEventListener('boat:save', save);
		window.removeEventListener('boat:save-as', saveAs);
	});

	// Update window title in Tauri mode
	$effect(() => {
		if ($appMode !== 'web' && treebank) {
			const dirty = $isDirty ? '[*] ' : '';
			const title = `${dirty}${treebank.title} — Sentence ${order} — BoAT`;
			import('@tauri-apps/api/webviewWindow').then(({ getCurrentWebviewWindow }) => {
				getCurrentWebviewWindow().setTitle(title);
			}).catch(() => {});
		}
	});

	// Auto-hide graph for sentences with >= 50 tokens (on initial load)
	let graphAutoHideApplied = $state(false);
	$effect(() => {
		if (!loading && tokenCount > 0 && !graphAutoHideApplied) {
			graphAutoHideApplied = true;
			// Only auto-hide if user hasn't explicitly set a localStorage preference
			const storedPref = localStorage.getItem('boat-show-graph');
			if (storedPref === null && tokenCount >= 50) {
				showGraph = false;
			}
		}
	});

	// Persist graph visibility preference to localStorage on manual toggle
	function toggleGraph() {
		showGraph = !showGraph;
		localStorage.setItem('boat-show-graph', showGraph ? '1' : '0');
	}

	// Warn before closing tab with unsaved changes
	$effect(() => {
		const dirty = $isDirty;
		function beforeUnload(e: BeforeUnloadEvent) {
			if (dirty) {
				e.preventDefault();
			}
		}
		window.addEventListener('beforeunload', beforeUnload);
		return () => window.removeEventListener('beforeunload', beforeUnload);
	});

	// Auto-save draft to localStorage when dirty (debounced 2s)
	$effect(() => {
		const dirty = $isDirty;
		const id = $annotationId;
		// Read cells to track changes
		$cells;
		if (!dirty || !id) return;
		const timeout = setTimeout(() => saveDraft(id), 2000);
		return () => clearTimeout(timeout);
	});

	async function loadPage() {
		loading = true;
		error = '';
		graphAutoHideApplied = false;
		try {
			const tb = await getTreebankByTitle(treebankSlug);
			treebank = tb;
			const [detail, sents] = await Promise.all([
				getAnnotationByPosition(tb.id, order),
				listSentences(tb.id)
			]);
			loadAnnotation(detail);
			maxOrder = sents.length > 0 ? Math.max(...sents.map((s) => s.order)) : 0;

			// Restore draft if available
			const draft = loadDraft(detail.id);
			if (draft) {
				cells.set(draft);
				toast.info('Unsaved changes recovered');
			}

			// Fetch other users' annotations for cloning (web mode only)
			if (!offline) {
				try {
					const allAnnotations = await listSentenceAnnotations(detail.sentence_id);
					otherAnnotations = allAnnotations.filter(
						(a) => !a.is_template && a.annotator_id !== $user?.id
					);
				} catch {
					otherAnnotations = [];
				}
			}

			// Fetch validation profile (gracefully handle 404)
			try {
				validationProfile = await getValidationProfile(tb.id);
			} catch {
				validationProfile = null;
			}
		} catch (err) {
			error = err instanceof ApiError ? err.detail : 'Failed to load annotation';
		} finally {
			loading = false;
		}
	}

	async function save() {
		if ($isSaving) return;
		if (!$annotationId || !treebank) return;
		isSaving.set(true);
		try {
			await updateWordlines($annotationId, getCellsForSave());
			await updateAnnotation($annotationId, {
				notes: $notes,
			});

			// In offline mode, also persist to disk
			if (offline) {
				const { invoke } = await import('@tauri-apps/api/core');
				await invoke('save_file');
			}

			const detail = await getAnnotationByPosition(treebank.id, order);
			loadAnnotation(detail);
			clearDraft(detail.id);
			toast.success('Annotation saved');
		} catch (err) {
			const msg = err instanceof ApiError ? err.detail : 'Failed to save';
			toast.error(msg);
			error = msg;
		} finally {
			isSaving.set(false);
		}
	}

	async function saveAs() {
		if (!treebank) return;
		try {
			const { invoke } = await import('@tauri-apps/api/core');
			await invoke('save_file_as');
			toast.success('File saved');
		} catch (err) {
			if (err !== 'No file selected') {
				toast.error(String(err));
			}
		}
	}

	async function changeStatus(newStatus: number) {
		if ($isSaving || !$annotationId || !treebank) return;
		isSaving.set(true);
		try {
			await updateAnnotation($annotationId, { status: newStatus });
			const detail = await getAnnotationByPosition(treebank.id, order);
			loadAnnotation(detail);
			toast.success('Status updated');
		} catch (err) {
			const msg = err instanceof ApiError ? err.detail : 'Failed to update status';
			toast.error(msg);
		} finally {
			isSaving.set(false);
		}
	}

	async function goPrev() {
		if (loading) return;
		if (order <= 1) return;
		if ($isDirty && !confirm('You have unsaved changes. Continue?')) return;
		await goto(`/annotate/${treebankSlug}/${order - 1}`);
		await loadPage();
	}

	async function goNext() {
		if (loading) return;
		if (order >= maxOrder) return;
		if ($isDirty && !confirm('You have unsaved changes. Continue?')) return;
		await goto(`/annotate/${treebankSlug}/${order + 1}`);
		await loadPage();
	}

	async function handleClone(sourceAnnotationId: number) {
		if (cloning || !treebank) return;
		if ($isDirty && !confirm('You have unsaved changes that will be lost. Continue?')) return;
		cloning = true;
		try {
			await cloneAnnotation(sourceAnnotationId);
			// Reload the page to pick up the cloned wordlines
			const detail = await getAnnotationByPosition(treebank.id, order);
			loadAnnotation(detail);
			clearDraft(detail.id);
			toast.success('Annotation cloned');
		} catch (err) {
			const msg = err instanceof ApiError ? err.detail : 'Failed to clone annotation';
			toast.error(msg);
		} finally {
			cloning = false;
		}
	}

	function handleColumnsChange(cols: string[]) {
		visibleColumns = cols;
	}

	function handleTokenSelect(tokenId: string) {
		selectedTokenId = tokenId;
	}

	function handleGraphTokenClick(tokenId: string) {
		if (headSelectionMode && selectedTokenId && selectedTokenId !== tokenId) {
			// Set the HEAD of selectedTokenId to tokenId
			updateCell(selectedTokenId, 'head', tokenId);
			headSelectionMode = false;
		} else {
			selectedTokenId = tokenId;
		}
	}
</script>

<div class="flex h-screen flex-col">
	<!-- Header bar -->
	<div class="flex items-center justify-between border-b border-border bg-background px-4 py-2">
		<div class="flex items-center gap-4">
			<Breadcrumb crumbs={[
				{ label: offline ? 'Home' : 'Treebanks', href: offline ? '/desktop' : '/treebanks' },
				{ label: treebank?.title ?? '...', href: `/treebanks/${treebankSlug}` },
				{ label: `Sentence ${order}` },
			]} />
			<span class="text-sm font-mono text-muted-foreground">#{$sentId}</span>
		</div>
		<div class="flex items-center gap-3 text-sm">
			{#if maxOrder > 0}
				<span class="hidden sm:flex items-center gap-2 text-xs text-muted-foreground">
					Sentence {order} of {maxOrder}
					<span class="inline-block h-1.5 w-24 rounded-full bg-muted overflow-hidden">
						<span class="block h-full rounded-full bg-primary transition-all" style="width: {Math.round((order / maxOrder) * 100)}%"></span>
					</span>
				</span>
			{/if}
			<Tooltip text="Toggle graph (Alt+G)">
				<button
					onclick={toggleGraph}
					class="text-muted-foreground hover:text-foreground cursor-pointer {showGraph ? 'text-primary' : ''}"
				>Graph</button>
			</Tooltip>
			<Tooltip text="Click-to-set HEAD (Alt+H)">
				<button
					onclick={() => { headSelectionMode = !headSelectionMode; }}
					class="cursor-pointer {headSelectionMode ? 'text-primary font-medium' : 'text-muted-foreground hover:text-foreground'}"
				>{headSelectionMode ? 'HEAD mode ON' : 'Set HEAD'}</button>
			</Tooltip>
			{#if !offline}
				<Tooltip text="Toggle discussion (Alt+D)">
					<button
						onclick={() => (showComments = !showComments)}
						class="text-muted-foreground hover:text-foreground cursor-pointer {showComments ? 'text-primary' : ''}"
					>Discussion</button>
				</Tooltip>
			{/if}
			<Tooltip text="Keyboard shortcuts (?)">
				<button
					onclick={() => (showShortcuts = true)}
					class="text-muted-foreground hover:text-foreground cursor-pointer rounded border border-border px-1.5 py-0.5 text-xs font-mono"
				>?</button>
			</Tooltip>
			<a href={offline ? '/desktop' : '/dashboard'} class="text-muted-foreground hover:text-foreground">Home</a>
		</div>
	</div>

	{#if headSelectionMode}
		<div class="flex items-center gap-3 border-b border-primary/30 bg-primary/5 px-4 py-2 text-sm">
			<span class="font-medium text-primary">HEAD selection mode</span>
			{#if selectedTokenId}
				<span class="text-muted-foreground">Token <strong class="text-foreground">{selectedTokenId}</strong> selected — click another token in the graph to set as its HEAD</span>
			{:else}
				<span class="text-muted-foreground">Click a token in the table to select it, then click its HEAD in the graph</span>
			{/if}
			<button
				onclick={() => (headSelectionMode = false)}
				class="ml-auto rounded-md border border-border bg-background px-2 py-0.5 text-xs text-muted-foreground hover:text-foreground cursor-pointer"
			>Cancel <kbd class="ml-1 rounded bg-muted px-1 font-mono text-[10px]">Esc</kbd></button>
		</div>
	{/if}

	{#if loading}
		<div class="flex flex-1 items-center justify-center">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
		</div>
	{:else if error}
		<div class="flex flex-1 items-center justify-center p-8">
			<ErrorState message={error} onRetry={loadPage} />
		</div>
	{:else}
		{#if showHints}
			<div class="flex items-center gap-3 border-b border-border bg-accent px-4 py-2 text-xs text-muted-foreground">
				<span class="font-medium text-foreground">Tips:</span>
				<span>Use <kbd class="rounded bg-muted px-1 font-mono">Alt+H</kbd> for HEAD mode</span>
				<span class="text-border">|</span>
				<span>Toggle columns in the toolbar below</span>
				<span class="text-border">|</span>
				<span>Press <kbd class="rounded bg-muted px-1 font-mono">?</kbd> for all shortcuts</span>
				<button
					onclick={() => { showHints = false; localStorage.setItem('boat-hints-dismissed', '1'); }}
					class="ml-auto cursor-pointer text-muted-foreground hover:text-foreground"
				>&times;</button>
			</div>
		{/if}

		<!-- Sentence text -->
		<div class="border-b border-border bg-muted/30 px-4 py-3">
			<p class="text-sm">{$sentenceText}</p>
			{#if $sentenceMetadata}
				<div class="mt-1 flex flex-wrap gap-2">
					{#each Object.entries($sentenceMetadata) as [key, val]}
						<span class="rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
							{key}: {val}
						</span>
					{/each}
				</div>
			{/if}
			{#if otherAnnotations.length > 0}
				<div class="mt-2 flex items-center gap-2 text-xs">
					<span class="text-muted-foreground">Clone from:</span>
					{#each otherAnnotations as anno}
						<button
							onclick={() => handleClone(anno.id)}
							disabled={cloning}
							class="rounded border border-border bg-background px-2 py-0.5 text-xs text-muted-foreground hover:text-foreground hover:border-primary cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
						>{anno.annotator_username ?? `user #${anno.annotator_id}`}</button>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Main content -->
		<div class="flex flex-1 overflow-hidden">
			<!-- Annotation editor -->
			<div class="flex flex-1 flex-col overflow-hidden">
				<div class="p-3">
					<AnnotationToolbar
						bind:visibleColumns
						onsave={save}
						onstatuschange={changeStatus}
						onnext={goNext}
						onprev={goPrev}
						oncolumnschange={handleColumnsChange}
						hasPrev={order > 1}
						hasNext={order < maxOrder}
						{loading}
					/>
					{#if validationErrorCount > 0}
						<button
							onclick={() => {
								const firstKey = validationErrors.keys().next().value;
								if (firstKey) {
									const tokenId = firstKey.split(':')[0];
									const el = document.querySelector('[aria-label*="token ' + tokenId + '"]');
									el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
								}
							}}
							class="mt-1 inline-flex items-center gap-1.5 rounded-full bg-destructive/10 px-2.5 py-1 text-xs font-medium text-destructive hover:bg-destructive/20 cursor-pointer transition-colors"
							title="Click to scroll to first error"
						>
							<span class="inline-block h-1.5 w-1.5 rounded-full bg-destructive"></span>
							{validationErrorCount} {validationErrorCount === 1 ? 'error' : 'errors'}
						</button>
					{/if}
				</div>

				<div class="flex-1 overflow-auto px-3 pb-3">
					<!-- Graph above table (hybrid layout) -->
					{#if showGraph}
						<div class="mb-2 rounded-lg border border-border bg-background p-2">
							<DisplacyGraph
								{visibleColumns}
								{selectedTokenId}
								{headSelectionMode}
								onTokenClick={handleGraphTokenClick}
								exportFilename={`${treebankSlug}_${$sentId}`}
							/>
						</div>
					{:else if tokenCount >= 50}
						<div class="mb-2 flex items-center gap-2 rounded-lg border border-dashed border-border bg-muted/20 px-3 py-2">
							<span class="text-xs text-muted-foreground">Graph hidden ({tokenCount} tokens).</span>
							<button
								onclick={toggleGraph}
								class="text-xs text-primary hover:underline cursor-pointer"
							>Show graph</button>
						</div>
					{/if}

					<!-- Annotation table -->
					<AnnotationTable
						{visibleColumns}
						{selectedTokenId}
						{validationProfile}
						{validationErrors}
						onTokenSelect={handleTokenSelect}
					/>
				</div>
			</div>

			<!-- Comments panel (toggleable, web/connected only) -->
			{#if showComments && !offline}
				<div class="w-80 border-l border-border overflow-auto">
					<CommentsPanel />
				</div>
			{/if}
		</div>
	{/if}
</div>

<KeyboardShortcutsModal
	open={showShortcuts}
	shortcuts={shortcutManager.getShortcuts()}
	onclose={() => (showShortcuts = false)}
/>
