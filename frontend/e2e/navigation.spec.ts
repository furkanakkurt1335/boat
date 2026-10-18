import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
	test('home page loads', async ({ page }) => {
		await page.goto('/');

		await expect(page).toHaveTitle(/BoAT/);
	});

	test('navbar links work', async ({ page }) => {
		// The home page redirects to /login when unauthenticated,
		// so we check the login page for navigation links.
		await page.goto('/login');

		// Login page should have a link to the register page
		const registerLink = page.getByRole('link', { name: 'Register' });
		await expect(registerLink).toBeVisible();
		await expect(registerLink).toHaveAttribute('href', '/register');

		// Navigate to register and verify it has a link back to login
		await registerLink.click();
		await expect(page).toHaveURL(/\/register/);

		const signInLink = page.getByRole('link', { name: 'Sign in' });
		await expect(signInLink).toBeVisible();
		await expect(signInLink).toHaveAttribute('href', '/login');
	});
});
