import { api } from './client';
import type {
	RewriteApplyResponse,
	RewritePreviewResponse,
	RewriteRequest,
	SearchResponse,
	StructuralQuery,
	StructuralSearchResponse
} from './types';

export interface SearchQuery {
	field: string;
	value: string;
}

export function search(queries: SearchQuery[], treebankTitle?: string, offset = 0, limit = 20) {
	const params = new URLSearchParams();
	for (const q of queries) {
		params.append(q.field, q.value);
	}
	if (treebankTitle) params.set('treebank_title', treebankTitle);
	params.set('offset', String(offset));
	params.set('limit', String(limit));
	return api.get<SearchResponse>(`/search?${params}`);
}

export function searchStructural(query: StructuralQuery) {
	return api.post<StructuralSearchResponse>('/search/structural', query);
}

export function rewritePreview(body: RewriteRequest) {
	return api.post<RewritePreviewResponse>('/search/rewrite/preview', body);
}

export function rewriteApply(body: RewriteRequest) {
	return api.post<RewriteApplyResponse>('/search/rewrite/apply', body);
}
