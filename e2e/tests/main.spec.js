import { test, expect } from '@playwright/test';

test('environment variables are set', async () => {
  expect(process.env.OKTETO_NAMESPACE).toBeDefined();
  expect(process.env.OKTETO_DOMAIN).toBeDefined();
  expect(process.env.OKTETO_NAMESPACE).not.toBe('');
  expect(process.env.OKTETO_DOMAIN).not.toBe('');
});


test('menu has title', async ({ page }) => {
  await page.goto(`https://menu-${process.env.OKTETO_NAMESPACE}.${process.env.OKTETO_DOMAIN}`);

  // The page title
  await expect(page).toHaveTitle('The Oktaco Shop');
});

test('kitchen has title', async ({ page }) => {
  await page.goto(`https://menu-${process.env.OKTETO_NAMESPACE}.${process.env.OKTETO_DOMAIN}`);

  // The page title
  await expect(page).toHaveTitle('The Oktaco Shop');
});

test('check has title', async ({ page }) => {
  await page.goto(`https://check-${process.env.OKTETO_NAMESPACE}.${process.env.OKTETO_DOMAIN}`);

  // The page title
  await expect(page).toHaveTitle('The Oktaco Shop - Check');
});


test('menu input has correct placeholder', async ({ page }) => {
  await page.goto(`https://menu-${process.env.OKTETO_NAMESPACE}.${process.env.OKTETO_DOMAIN}`);

  const menuInput = await page.locator('input#item');
  await expect(menuInput).toBeVisible();
  await expect(menuInput).toHaveAttribute('placeholder', 'Tacos, burritos, churros...');
});
