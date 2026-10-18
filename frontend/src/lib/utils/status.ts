import { AnnotationStatus } from '$api/types';

interface StatusConfig {
	label: string;
	color: string;
	dot: string;
}

const STATUS_CONFIGS: Record<number, StatusConfig> = {
	[AnnotationStatus.NEW]: {
		label: 'New',
		color: 'bg-muted text-muted-foreground',
		dot: 'bg-muted-foreground'
	},
	[AnnotationStatus.DRAFT]: {
		label: 'Draft',
		color: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400',
		dot: 'bg-yellow-500'
	},
	[AnnotationStatus.SUBMITTED]: {
		label: 'Submitted',
		color: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
		dot: 'bg-blue-500'
	},
	[AnnotationStatus.APPROVED]: {
		label: 'Approved',
		color: 'bg-success/10 text-success',
		dot: 'bg-success'
	},
	[AnnotationStatus.REJECTED]: {
		label: 'Rejected',
		color: 'bg-destructive/10 text-destructive',
		dot: 'bg-destructive'
	}
};

const UNKNOWN: StatusConfig = {
	label: 'Unknown',
	color: 'bg-muted text-muted-foreground',
	dot: 'bg-muted-foreground'
};

export function getStatusConfig(status: number): StatusConfig {
	return STATUS_CONFIGS[status] ?? UNKNOWN;
}
