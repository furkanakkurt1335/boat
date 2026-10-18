import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
	test('register page loads', async ({ page }) => {
		await page.goto('/register');

		await expect(page.getByRole('heading', { name: 'Create account' })).toBeVisible();
		await expect(page.getByLabel('First name')).toBeVisible();
		await expect(page.getByLabel('Last name')).toBeVisible();
		await expect(page.getByLabel('Username')).toBeVisible();
		await expect(page.getByLabel('Email')).toBeVisible();
		await expect(page.getByLabel('Password', { exact: true })).toBeVisible();
		await expect(page.getByLabel('Confirm password')).toBeVisible();
		await expect(page.getByRole('button', { name: 'Register' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Sign in' })).toBeVisible();
	});

	test('login page loads', async ({ page }) => {
		await page.goto('/login');

		await expect(page.getByRole('heading', { name: 'BoAT' })).toBeVisible();
		await expect(page.getByText('Boğaziçi University Annotation Tool')).toBeVisible();
		await expect(page.getByLabel('Username')).toBeVisible();
		await expect(page.getByLabel('Password')).toBeVisible();
		await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
		await expect(page.getByRole('link', { name: 'Register' })).toBeVisible();
	});

	test('login with invalid credentials shows error', async ({ page }) => {
		await page.goto('/login');

		await page.getByLabel('Username').fill('nonexistent_user');
		await page.getByLabel('Password').fill('wrong_password');
		await page.getByRole('button', { name: 'Sign in' }).click();

		await expect(page.getByRole('alert')).toBeVisible({ timeout: 10_000 });
	});

	test('redirect to login when unauthenticated', async ({ page }) => {
		await page.goto('/dashboard');

		await expect(page).toHaveURL(/\/login/, { timeout: 10_000 });
	});
});
