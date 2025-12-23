export const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';

export const AUTHOR_USERNAME = process.env.AUTHOR_USERNAME || 'author01';
export const AUTHOR_PASSWORD = process.env.AUTHOR_PASSWORD || 'P@ssword1234';

export const REVIEWER_USERNAME = process.env.REVIEWER_USERNAME || 'reviewer01';
export const REVIEWER_PASSWORD = process.env.REVIEWER_PASSWORD || 'P@ssword1234';

export const APPROVER_USERNAME = process.env.APPROVER_USERNAME || 'approver01';
export const APPROVER_PASSWORD = process.env.APPROVER_PASSWORD || 'P@ssword1234';

// IDs for selectOption; prefer using visible labels where possible. These are fallbacks.
export const DOC_TYPE_ID = process.env.DOC_TYPE_ID || '1';
export const DOC_SOURCE_ID = process.env.DOC_SOURCE_ID || '1';
export const REVIEWER_ID = process.env.REVIEWER_ID || '119';
export const APPROVER_ID = process.env.APPROVER_ID || '120';
