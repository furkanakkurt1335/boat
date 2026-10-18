import { api } from './client';
import type { Token, UserRead } from './types';

export function login(username: string, password: string) {
	return api.post<Token>('/auth/login', { username, password });
}

export function register(data: {
	username: string;
	email: string;
	password: string;
	first_name: string;
	last_name: string;
}) {
	return api.post<UserRead>('/auth/register', data);
}

export function getMe() {
	return api.get<UserRead>('/auth/me');
}

export function updateMe(data: Partial<{ first_name: string; last_name: string; email: string; preferences: Record<string, unknown> }>) {
	return api.patch<UserRead>('/auth/me', data);
}
