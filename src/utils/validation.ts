/**
 * Input validation utilities for BioLink frontend.
 * All user inputs should be validated before API submission.
 */

const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
const VALID_COHORTS = ['BHS', 'EHVol', 'ALL'];

export function validateEmail(email: string): boolean {
  if (!email || email.length > 254) return false;
  return EMAIL_REGEX.test(email);
}

export function validatePassword(password: string): boolean {
  if (!password || password.length < 12) return false;
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasNumber = /\d/.test(password);
  const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
  return hasUpper && hasLower && hasNumber && hasSpecial;
}

export function validatePatientSearch(params: {
  query?: string;
  min_age?: number;
  max_age?: number;
  cohort?: string;
}): boolean {
  if (params.min_age !== undefined && (params.min_age < 0 || params.min_age > 120)) {
    return false;
  }
  if (params.max_age !== undefined && (params.max_age < 0 || params.max_age > 120)) {
    return false;
  }
  if (params.min_age !== undefined && params.max_age !== undefined && params.min_age > params.max_age) {
    return false;
  }
  if (params.cohort && !VALID_COHORTS.includes(params.cohort)) {
    return false;
  }
  return true;
}

export function sanitizeInput(input: string): string {
  if (!input) return '';
  // Remove HTML tags
  const withoutHtml = input.replace(/<[^>]*>/g, '');
  // Trim whitespace
  return withoutHtml.trim();
}

export function validateCohortName(name: string): boolean {
  if (!name || name.length < 3 || name.length > 100) return false;
  // Only allow alphanumeric, spaces, hyphens, underscores
  return /^[a-zA-Z0-9\s_-]+$/.test(name);
}
