export const UPOS_TAGS = [
	'ADJ', 'ADP', 'ADV', 'AUX', 'CCONJ', 'DET', 'INTJ', 'NOUN',
	'NUM', 'PART', 'PRON', 'PROPN', 'PUNCT', 'SCONJ', 'SYM', 'VERB', 'X'
] as const;

export const DEPREL_TAGS = [
	'acl', 'acl:relcl', 'advcl', 'advmod', 'amod', 'appos', 'aux', 'aux:pass',
	'case', 'cc', 'ccomp', 'clf', 'compound', 'conj', 'cop', 'csubj',
	'csubj:pass', 'dep', 'det', 'discourse', 'dislocated', 'expl', 'fixed',
	'flat', 'flat:name', 'goeswith', 'iobj', 'list', 'mark', 'nmod',
	'nmod:poss', 'nsubj', 'nsubj:pass', 'nummod', 'obj', 'obl', 'obl:tmod',
	'orphan', 'parataxis', 'punct', 'reparandum', 'root', 'vocative', 'xcomp'
] as const;

// Feature inventory per language (extensible)
export const FEATURES: Record<string, string[]> = {
	Case: ['Abl', 'Acc', 'Dat', 'Gen', 'Ins', 'Loc', 'Nom'],
	Number: ['Plur', 'Sing'],
	'Number[psor]': ['Plur', 'Sing'],
	Person: ['1', '2', '3'],
	'Person[psor]': ['1', '2', '3'],
	Tense: ['Aor', 'Fut', 'Past', 'Pqp', 'Pres'],
	Aspect: ['Hab', 'Imp', 'Perf', 'Prog'],
	Mood: ['Cnd', 'Des', 'Gen', 'Imp', 'Ind', 'Nec', 'Opt', 'Pot'],
	Voice: ['Cau', 'CauPass', 'Pass', 'Rcp', 'Rfl'],
	Polarity: ['Neg', 'Pos'],
	Gender: ['Fem', 'Masc', 'Neut'],
	Definite: ['Def', 'Ind'],
	PronType: ['Art', 'Dem', 'Ind', 'Int', 'Neg', 'Prs', 'Rcp', 'Rel', 'Tot'],
	NumType: ['Card', 'Dist', 'Ord'],
	Degree: ['Cmp', 'Pos', 'Sup'],
	VerbForm: ['Conv', 'Fin', 'Inf', 'Part', 'Vnoun'],
	Evident: ['Fh', 'Nfh'],
	Reflex: ['Yes'],
	Foreign: ['Yes'],
	Abbr: ['Yes'],
	Typo: ['Yes'],
};

// Default MISC attributes (fallback when no validation profile)
export const DEFAULT_MISC: Record<string, string[] | null> = {
	SpaceAfter: ['No'],
	SpacesAfter: null,
	Translit: null,
	LTranslit: null,
	Gloss: null,
	CorrectForm: null,
	CorrectSpaceAfter: ['No'],
	Lang: null,
};

export type UposTag = (typeof UPOS_TAGS)[number];
export type DeprelTag = (typeof DEPREL_TAGS)[number];
