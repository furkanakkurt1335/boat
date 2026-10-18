// Auth
export interface UserRead {
	id: number;
	username: string;
	email: string;
	first_name: string;
	last_name: string;
	is_active: boolean;
	is_admin: boolean;
	preferences: UserPreferences;
}

export interface UserPreferences {
	graph_preference: number;
	error_condition: boolean;
	current_columns: string[];
}

export interface Token {
	access_token: string;
	token_type: string;
}

// Treebank
export interface TreebankRead {
	id: number;
	title: string;
	language: string;
	created_by: number | null;
	created_at: string;
}

export interface TreebankWithProgress extends TreebankRead {
	sentence_count: number;
	annotation_count: number;
	complete_count: number;
}

// Sentence
export interface SentenceBrief {
	id: number;
	order: number;
	sent_id: string;
	text: string;
	metadata: Record<string, string> | null;
}

export interface SentenceRead extends SentenceBrief {
	treebank_id: number;
	metadata: Record<string, string> | null;
	created_at: string;
}

// WordLine
export interface WordLineRead {
	id: number;
	annotation_id: number;
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
	feats_parsed: Record<string, string> | null;
	misc_parsed: Record<string, string> | null;
}

// Annotation
export const AnnotationStatus = {
	NEW: 0,
	DRAFT: 1,
	SUBMITTED: 2,
	APPROVED: 3,
	REJECTED: 4
} as const;

export type AnnotationStatusValue = (typeof AnnotationStatus)[keyof typeof AnnotationStatus];

export interface AnnotationRead {
	id: number;
	sentence_id: number;
	annotator_id: number;
	status: number;
	status_label: string;
	is_template: boolean;
	is_gold: boolean;
	notes: string;
	created_at: string;
	annotator_username: string | null;
}

export interface AnnotationDetail extends AnnotationRead {
	wordlines: WordLineRead[];
	annotator_username: string | null;
	sentence_sent_id: string | null;
	sentence_text: string | null;
	sentence_metadata: Record<string, string> | null;
	treebank_title: string | null;
	treebank_id: number | null;
	treebank_created_by: number | null;
	sentence_order: number | null;
}

// Search
export interface SearchResult {
	id: number;
	annotation_id: number;
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
	feats_parsed: Record<string, string> | null;
	misc_parsed: Record<string, string> | null;
	sentence_sent_id: string;
	sentence_text: string;
	treebank_title: string;
	annotator_username: string;
}

export interface SearchResponse {
	results: SearchResult[];
	total: number;
}

// Structural Search
export interface NodeConstraint {
	upos?: string[];
	feats?: Record<string, string[]>;
	form?: string;
	lemma?: string;
}

export interface RelationConstraint extends NodeConstraint {
	deprel?: string[];
}

export interface StructuralQuery {
	target: NodeConstraint;
	head_constraint?: RelationConstraint;
	dependent_constraints?: RelationConstraint[];
	negated_dependents?: RelationConstraint[];
	treebank_id?: number;
	limit?: number;
	offset?: number;
}

export interface StructuralMatch {
	sentence_id: number;
	sent_id: string;
	text: string;
	treebank_id: number;
	treebank_title: string;
	matched_token_ids: string[];
}

export interface StructuralSearchResponse {
	results: StructuralMatch[];
	total: number;
}

// Batch Rewrite
export interface RewriteRequest {
	pattern: string;
	operations: string[];
	treebank_id?: number;
	annotation_scope: 'template' | 'mine' | 'all';
}

export interface RewriteChange {
	sentence_id: number;
	sent_id: string;
	token_id: string;
	form: string;
	node_name: string;
	descriptions: string[];
}

export interface RewritePreviewResponse {
	changes: RewriteChange[];
	total_tokens: number;
	total_sentences: number;
}

export interface RewriteApplyResponse {
	applied: number;
	skipped: number;
	changes: RewriteChange[];
}

// Comment
export interface CommentRead {
	id: number;
	sentence_id: number;
	user_id: number;
	username: string;
	text: string;
	created_at: string;
}

// Diff (adjudication)
export interface DiffAnnotator {
	username: string;
	annotation_id: number;
	values: Record<string, string> | null;
}

export interface DiffToken {
	id_f: string;
	annotators: DiffAnnotator[];
	disagreements: string[];
}

export interface DiffResponse {
	sentence_id: number;
	annotator_count: number;
	token_count: number;
	disagreement_count: number;
	tokens: DiffToken[];
}

// Validation Profile
export interface ValidationProfileRead {
	id: number;
	treebank_id: number | null;
	allowed_upos: string[] | null;
	allowed_deprels: string[] | null;
	allowed_features: Record<string, string[]> | null;
	allowed_misc: Record<string, string[] | null> | null;
	feature_order: string[] | null;
	custom_rules: Record<string, unknown>[] | null;
	created_at: string;
}

// Statistics
export interface TreebankStats {
	upos_distribution: Record<string, number>;
	deprel_distribution: Record<string, number>;
	top_lemmas: { lemma: string; count: number }[];
	sentence_lengths: number[];
	total_tokens: number;
	total_sentences: number;
}

// Agreement
export interface AgreementResponse {
	treebank_id: number;
	agreement: number;
	sentences_scored: number;
}
