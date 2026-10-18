import { api } from './client';
import type { ValidationProfileRead } from './types';

export function getValidationProfile(treebankId: number) {
	return api.get<ValidationProfileRead>(`/validation-profiles/${treebankId}`);
}

export function updateValidationProfile(profileId: number, data: Partial<ValidationProfileRead>) {
	return api.patch<ValidationProfileRead>(`/validation-profiles/${profileId}`, data);
}
