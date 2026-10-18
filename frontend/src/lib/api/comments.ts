import { api } from './client';
import type { CommentRead } from './types';

export function listComments(sentenceId: number) {
	return api.get<CommentRead[]>(`/sentences/${sentenceId}/comments`);
}

export function createComment(sentenceId: number, text: string) {
	return api.post<CommentRead>(`/sentences/${sentenceId}/comments`, { text });
}

export function deleteComment(sentenceId: number, commentId: number) {
	return api.del(`/sentences/${sentenceId}/comments/${commentId}`);
}
