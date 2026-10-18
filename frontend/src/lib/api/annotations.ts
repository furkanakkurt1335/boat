import { api } from './client';
import type { AnnotationRead, AnnotationDetail, WordLineRead } from './types';

export function createAnnotation(sentenceId: number) {
	return api.post<AnnotationRead>('/annotations', { sentence_id: sentenceId });
}

export function cloneAnnotation(annotationId: number) {
	return api.post<AnnotationRead>(`/annotations/${annotationId}/clone`);
}

export function getAnnotation(id: number) {
	return api.get<AnnotationDetail>(`/annotations/${id}`);
}

export function getAnnotationByPosition(treebankId: number, order: number) {
	return api.get<AnnotationDetail>(`/annotations/by-position/?treebank_id=${treebankId}&order=${order}`);
}

export function updateAnnotation(id: number, data: { status?: number; notes?: string; is_gold?: boolean }) {
	return api.patch<AnnotationRead>(`/annotations/${id}`, data);
}

export function deleteAnnotation(id: number) {
	return api.del(`/annotations/${id}`);
}

export function getMyAnnotations(status?: number) {
	const qs = status !== undefined ? `?status=${status}` : '';
	return api.get<AnnotationDetail[]>(`/annotations/mine/${qs}`);
}

export function getWordlines(annotationId: number) {
	return api.get<WordLineRead[]>(`/wordlines/annotations/${annotationId}`);
}

export function updateWordlines(
	annotationId: number,
	wordlines: Array<{
		id_f: string;
		form: string;
		lemma: string;
		upos: string;
		xpos: string;
		feats: string;
		head: string;
		deprel: string;
		deps: string;
		misc: string;
	}>
) {
	return api.put<WordLineRead[]>(`/wordlines/annotations/${annotationId}`, { wordlines });
}
