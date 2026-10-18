import { derived } from 'svelte/store';
import { user } from './auth';

export const GRAPH_OPTIONS = [
	{ value: 0, label: 'None' },
	{ value: 1, label: 'conllu.js (horizontal)' }
] as const;

export const ALL_COLUMNS = [
	'ID', 'FORM', 'LEMMA', 'UPOS', 'XPOS', 'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC'
] as const;

export const DEFAULT_COLUMNS = ['ID', 'FORM', 'LEMMA', 'UPOS', 'XPOS', 'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC'];

export const graphPreference = derived(user, ($user) =>
	$user?.preferences?.graph_preference ?? 1
);

export const errorCondition = derived(user, ($user) =>
	$user?.preferences?.error_condition ?? true
);

export const currentColumns = derived(user, ($user) =>
	$user?.preferences?.current_columns ?? DEFAULT_COLUMNS
);
