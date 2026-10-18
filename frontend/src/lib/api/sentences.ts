import { api } from './client';
import type { SentenceBrief, SentenceRead, AnnotationRead, DiffResponse } from './types';

export function listSentences(treebankId: number) {
	return api.get<SentenceBrief[]>(`/treebanks/${treebankId}/sentences`);
}

export function getSentence(id: number) {
	return api.get<SentenceRead>(`/sentences/${id}`);
}

export function createSentence(treebankId: number, sentId: string, text: string) {
	return api.post<SentenceRead>(`/sentences?treebank_id=${treebankId}`, { sent_id: sentId, text });
}

export function deleteSentence(id: number) {
	return api.del(`/sentences/${id}`);
}

export function listSentenceAnnotations(id: number) {
	return api.get<AnnotationRead[]>(`/sentences/${id}/annotations`);
}

export function getSentenceDiff(id: number) {
	return api.get<DiffResponse>(`/sentences/${id}/diff`);
}
