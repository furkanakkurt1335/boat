<script lang="ts">
	import { cells, updateCell, type Cell, type CellField } from '$stores/annotation';
	import { toast } from '$stores/toast';
	import { Download, Image } from 'lucide-svelte';

	interface Props {
		visibleColumns: string[];
		selectedTokenId?: string | null;
		onTokenClick?: (tokenId: string) => void;
		headSelectionMode?: boolean;
		exportFilename?: string;
	}

	let {
		visibleColumns,
		selectedTokenId = null,
		onTokenClick,
		headSelectionMode = false,
		exportFilename = 'dependency-tree'
	}: Props = $props();

	// Layout constants
	const TOKEN_H = 28;
	const TOKEN_PAD_X = 12;
	const TOKEN_GAP = 8;
	const ARC_LAYER_H = 30;
	const ARC_PAD_TOP = 12;
	const LABEL_FONT = 10;
	const TOKEN_FONT = 13;
	const DEPREL_COLORS: Record<string, string> = {
		nsubj: '#3b82f6', 'nsubj:pass': '#3b82f6',
		obj: '#22c55e', iobj: '#16a34a',
		obl: '#eab308', 'obl:tmod': '#eab308',
		advmod: '#a855f7', amod: '#ec4899',
		nmod: '#f97316', 'nmod:poss': '#f97316',
		det: '#06b6d4', case: '#64748b',
		mark: '#78716c', cc: '#78716c',
		conj: '#ef4444', punct: '#94a3b8',
		root: '#dc2626', dep: '#6b7280',
		cop: '#f472b6', aux: '#a78bfa', 'aux:pass': '#a78bfa',
		xcomp: '#14b8a6', ccomp: '#0d9488',
		acl: '#fb923c', 'acl:relcl': '#fb923c',
		advcl: '#fbbf24', appos: '#f87171',
		flat: '#818cf8', 'flat:name': '#818cf8',
		compound: '#c084fc', fixed: '#e879f9',
		nummod: '#4ade80', discourse: '#d946ef',
		vocative: '#f43f5e', expl: '#be185d',
		parataxis: '#84cc16', orphan: '#ef4444',
		list: '#0ea5e9', dislocated: '#7c3aed',
		reparandum: '#b91c1c', goeswith: '#6b7280',
		clf: '#0891b2',
	};
	const DEFAULT_ARC_COLOR = '#94a3b8';

	// Measure text widths using a canvas context
	let canvas: HTMLCanvasElement | undefined;
	function measureText(text: string, fontSize: number): number {
		if (!canvas) canvas = document.createElement('canvas');
		const ctx = canvas.getContext('2d')!;
		ctx.font = `${fontSize}px system-ui, sans-serif`;
		return ctx.measureText(text).width;
	}

	interface TokenLayout {
		id_f: string;
		form: string;
		x: number; // center
		width: number;
		head: string;
		deprel: string;
	}

	interface Arc {
		from: number; // token index
		to: number;   // head token index
		label: string;
		level: number;
		color: string;
	}

	// Compute layout from current cells
	const layout = $derived.by(() => {
		const tokenCells = $cells.filter((c) => !c.id_f.includes('-') && !c.id_f.includes('.'));
		if (tokenCells.length === 0) return { tokens: [], arcs: [], width: 0, height: 0 };

		// Position tokens
		let x = TOKEN_PAD_X;
		const tokens: TokenLayout[] = tokenCells.map((c) => {
			const tw = Math.max(measureText(c.form, TOKEN_FONT), 20) + TOKEN_PAD_X * 2;
			const tok: TokenLayout = {
				id_f: c.id_f,
				form: c.form,
				x: x + tw / 2,
				width: tw,
				head: c.head,
				deprel: c.deprel,
			};
			x += tw + TOKEN_GAP;
			return tok;
		});

		const totalWidth = x + TOKEN_PAD_X;

		// Build arcs and compute levels (height based on span distance)
		const idToIndex = new Map(tokens.map((t, i) => [t.id_f, i]));
		const arcs: Arc[] = [];
		const spanDistances: number[] = [];

		for (let i = 0; i < tokens.length; i++) {
			const t = tokens[i];
			if (t.head === '_' || t.head === '0') continue;
			const headIdx = idToIndex.get(t.head);
			if (headIdx === undefined) continue;
			const span = Math.abs(i - headIdx);
			spanDistances.push(span);
		}

		// Assign levels: group by span distance, assign levels to avoid collisions
		const levelMap = new Map<string, number>();
		// Sort arcs by span distance (shorter first), assign levels greedily
		const arcData: Array<{ from: number; to: number; label: string; span: number; color: string }> = [];

		for (let i = 0; i < tokens.length; i++) {
			const t = tokens[i];
			if (t.head === '_' || t.head === '0') continue;
			const headIdx = idToIndex.get(t.head);
			if (headIdx === undefined) continue;
			const span = Math.abs(i - headIdx);
			const label = t.deprel === '_' ? '' : t.deprel;
			const color = (label ? DEPREL_COLORS[label] ?? DEPREL_COLORS[label.split(':')[0]] : undefined) ?? DEFAULT_ARC_COLOR;
			arcData.push({ from: i, to: headIdx, label, span, color });
		}

		arcData.sort((a, b) => a.span - b.span);

		// Greedy level assignment: track which ranges are occupied at each level
		const levelOccupied: Array<Array<[number, number]>> = [];

		for (const ad of arcData) {
			const lo = Math.min(ad.from, ad.to);
			const hi = Math.max(ad.from, ad.to);
			let level = 0;
			while (true) {
				if (!levelOccupied[level]) levelOccupied[level] = [];
				const conflict = levelOccupied[level].some(
					([a, b]) => !(hi <= a || lo >= b)
				);
				if (!conflict) break;
				level++;
			}
			levelOccupied[level] = levelOccupied[level] || [];
			levelOccupied[level].push([lo, hi]);
			arcs.push({ from: ad.from, to: ad.to, label: ad.label, level, color: ad.color });
		}

		const maxLevel = arcs.length > 0 ? Math.max(...arcs.map((a) => a.level)) : 0;
		const arcHeight = (maxLevel + 1) * ARC_LAYER_H + ARC_PAD_TOP;
		const totalHeight = arcHeight + TOKEN_H + 8;

		return { tokens, arcs, width: totalWidth, height: totalHeight, arcHeight };
	});

	function arcPath(arc: Arc, baseY: number): string {
		const tokens = layout.tokens;
		const fromX = tokens[arc.from].x;
		const toX = tokens[arc.to].x;
		const peakY = baseY - (arc.level + 1) * ARC_LAYER_H;

		return `M ${fromX} ${baseY} C ${fromX} ${peakY}, ${toX} ${peakY}, ${toX} ${baseY}`;
	}

	function labelPos(arc: Arc, baseY: number): { x: number; y: number } {
		const tokens = layout.tokens;
		const fromX = tokens[arc.from].x;
		const toX = tokens[arc.to].x;
		const peakY = baseY - (arc.level + 1) * ARC_LAYER_H;
		return { x: (fromX + toX) / 2, y: peakY - 3 };
	}

	const arcBaseY = $derived(layout.arcHeight ?? 0);

	function rootArcs(): Array<{ tokenIdx: number; deprel: string }> {
		return layout.tokens
			.map((t, i) => ({ tokenIdx: i, deprel: t.deprel, head: t.head }))
			.filter((t) => t.head === '0');
	}

	function handleTokenClick(tokenId: string) {
		onTokenClick?.(tokenId);
	}

	function cloneSvgForExport(): SVGSVGElement | null {
		const svgEl = document.getElementById('dep-graph-svg') as SVGSVGElement | null;
		if (!svgEl) return null;

		const clone = svgEl.cloneNode(true) as SVGSVGElement;

		// Detect dark mode
		const isDark = document.documentElement.classList.contains('dark');
		const bgColor = isDark ? '#0a0a0a' : '#ffffff';
		const textColor = isDark ? '#fafafa' : '#0a0a0a';

		// Inline computed styles on all elements (before inserting bgRect to keep indices aligned)
		const srcElements = svgEl.querySelectorAll('*');
		const cloneElements = clone.querySelectorAll('*');
		const styleProps = ['fill', 'stroke', 'stroke-width', 'opacity', 'font-size', 'font-family', 'font-weight', 'text-anchor'];
		for (let i = 0; i < srcElements.length; i++) {
			const computed = window.getComputedStyle(srcElements[i]);
			for (const prop of styleProps) {
				const val = computed.getPropertyValue(prop);
				if (val) (cloneElements[i] as SVGElement).style.setProperty(prop, val);
			}
		}

		// Set text color on token text elements (they use currentColor)
		clone.querySelectorAll('text').forEach((t) => {
			if (t.getAttribute('fill') === 'currentColor' || t.style.fill === 'currentColor') {
				t.style.fill = textColor;
			}
		});

		// Add background rect as first child (after style inlining)
		const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
		bgRect.setAttribute('width', '100%');
		bgRect.setAttribute('height', '100%');
		bgRect.setAttribute('fill', bgColor);
		clone.insertBefore(bgRect, clone.firstChild);

		// Set xmlns for standalone SVG
		clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
		clone.removeAttribute('class');

		return clone;
	}

	function triggerDownload(url: string, filename: string) {
		const a = document.createElement('a');
		a.href = url;
		a.download = filename;
		a.click();
		URL.revokeObjectURL(url);
	}

	function handleExportSvg() {
		const clone = cloneSvgForExport();
		if (!clone) return;
		const serializer = new XMLSerializer();
		const svgString = '<?xml version="1.0" encoding="UTF-8"?>\n' + serializer.serializeToString(clone);
		const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
		triggerDownload(URL.createObjectURL(blob), `${exportFilename}.svg`);
		toast.success('SVG exported');
	}

	function handleExportPng() {
		const clone = cloneSvgForExport();
		if (!clone) return;

		const w = layout.width;
		const h = layout.height;
		const scale = 2; // 2x resolution for crisp output

		const serializer = new XMLSerializer();
		const svgString = serializer.serializeToString(clone);
		const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
		const url = URL.createObjectURL(svgBlob);

		const img = new window.Image();
		img.onload = () => {
			const cvs = document.createElement('canvas');
			cvs.width = w * scale;
			cvs.height = h * scale;
			const ctx = cvs.getContext('2d')!;
			ctx.scale(scale, scale);
			ctx.drawImage(img, 0, 0, w, h);
			URL.revokeObjectURL(url);

			cvs.toBlob((blob) => {
				if (!blob) return;
				triggerDownload(URL.createObjectURL(blob), `${exportFilename}.png`);
				toast.success('PNG exported');
			}, 'image/png');
		};
		img.onerror = () => {
			URL.revokeObjectURL(url);
			toast.error('PNG export failed');
		};
		img.src = url;
	}

	function handleExportLatex() {
		const tokens = layout.tokens;
		const lines: string[] = [
			'\\begin{dependency}',
			'  \\begin{deptext}[column sep=0.4cm]',
		];
		const forms = tokens.map((t) => t.form).join(' \\& ');
		lines.push(`    ${forms} \\\\`);
		lines.push('  \\end{deptext}');

		for (const t of tokens) {
			if (t.head === '0') {
				const idx = tokens.findIndex((tok) => tok.id_f === t.id_f) + 1;
				lines.push(`  \\deproot{${idx}}{${t.deprel}}`);
			} else if (t.head !== '_') {
				const depIdx = tokens.findIndex((tok) => tok.id_f === t.id_f) + 1;
				const headIdx = tokens.findIndex((tok) => tok.id_f === t.head) + 1;
				if (headIdx > 0) {
					lines.push(`  \\depedge{${headIdx}}{${depIdx}}{${t.deprel}}`);
				}
			}
		}
		lines.push('\\end{dependency}');

		const text = lines.join('\n');
		navigator.clipboard.writeText(text);
		toast.success('LaTeX copied to clipboard');
	}
</script>

{#if layout.tokens.length > 0}
	<div class="relative">
		{#if layout.arcs.length === 0 && rootArcs().length === 0}
			<p class="px-2 py-1 text-xs text-muted-foreground">
				Set HEAD values in the table below to see dependency arcs. Use <kbd class="rounded bg-muted px-1 font-mono text-[10px]">Set HEAD</kbd> mode to click-assign heads in the graph.
			</p>
		{/if}
		<!-- Export buttons -->
		<div class="absolute right-2 top-1 z-10 flex gap-1">
			<button
				onclick={handleExportSvg}
				class="flex items-center gap-1 rounded bg-muted px-2 py-0.5 text-[10px] text-muted-foreground hover:text-foreground cursor-pointer"
				title="Export as SVG"
			><Download size={10} />SVG</button>
			<button
				onclick={handleExportPng}
				class="flex items-center gap-1 rounded bg-muted px-2 py-0.5 text-[10px] text-muted-foreground hover:text-foreground cursor-pointer"
				title="Export as PNG"
			><Image size={10} />PNG</button>
			<button
				onclick={handleExportLatex}
				class="rounded bg-muted px-2 py-0.5 text-[10px] text-muted-foreground hover:text-foreground cursor-pointer"
				title="Copy LaTeX tikz-dependency code"
			>LaTeX</button>
		</div>

		<div class="overflow-x-auto">
			<svg
				id="dep-graph-svg"
				width={layout.width}
				height={layout.height}
				viewBox="0 0 {layout.width} {layout.height}"
				class="select-none"
				style="min-width: {Math.max(layout.width, layout.tokens.length * 50)}px;"
			>
				<!-- Arcs -->
				{#each layout.arcs as arc}
					<path
						d={arcPath(arc, arcBaseY)}
						fill="none"
						stroke={arc.color}
						stroke-width="1.5"
						opacity="0.8"
					/>
					<!-- Arrowhead -->
					{@const toX = layout.tokens[arc.to].x}
					{@const fromX = layout.tokens[arc.from].x}
					{@const y = arcBaseY}
					<polygon
						points="{toX - 3},{y - 2} {toX + 3},{y - 2} {toX},{y + 2}"
						fill={arc.color}
						opacity="0.8"
					/>
					<!-- Label -->
					{@const lp = labelPos(arc, arcBaseY)}
					<text
						x={lp.x}
						y={lp.y}
						text-anchor="middle"
						font-size={LABEL_FONT}
						fill={arc.color}
						font-weight="600"
					>{arc.label}</text>
				{/each}

				<!-- Root markers -->
				{#each rootArcs() as ra}
					{@const tx = layout.tokens[ra.tokenIdx].x}
					{@const y = arcBaseY}
					<line x1={tx} y1={0} x2={tx} y2={y} stroke="#dc2626" stroke-width="1.5" stroke-dasharray="3,3" />
					<text x={tx} y={10} text-anchor="middle" font-size={LABEL_FONT} fill="#dc2626" font-weight="600">
						{ra.deprel}
					</text>
				{/each}

				<!-- Tokens -->
				{#each layout.tokens as tok, i}
					{@const y = arcBaseY}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<g
						role="button"
						tabindex="-1"
						class="{headSelectionMode ? 'cursor-crosshair' : 'cursor-pointer'}"
						onclick={() => handleTokenClick(tok.id_f)}
					>
						<rect
							x={tok.x - tok.width / 2}
							y={y + 2}
							width={tok.width}
							height={TOKEN_H}
							rx="3"
							fill={tok.id_f === selectedTokenId ? '#dbeafe' : 'transparent'}
							stroke={tok.id_f === selectedTokenId ? '#3b82f6' : headSelectionMode ? '#93c5fd' : '#e5e5e5'}
							stroke-width={tok.id_f === selectedTokenId ? 2 : headSelectionMode ? 1.5 : 1}
							stroke-dasharray={headSelectionMode && tok.id_f !== selectedTokenId ? '3,2' : 'none'}
						/>
						<text
							x={tok.x}
							y={y + TOKEN_H / 2 + 6}
							text-anchor="middle"
							font-size={TOKEN_FONT}
							fill="currentColor"
						>{tok.form}</text>
					</g>
				{/each}
			</svg>
		</div>
	</div>
{/if}
