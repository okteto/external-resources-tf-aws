import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('https://menu-oktaco-pr-20.demo.okteto.dev');

  // The page title
  await expect(page).toHaveTitle('The Oktaco Shop');
});


test('menu input has correct placeholder', async ({ page }) => {
  await page.goto('https://menu-oktaco-pr-20.demo.okteto.dev');

  const menuInput = await page.locator('input#item');
  await expect(menuInput).toBeVisible();
  await expect(menuInput).toHaveAttribute('placeholder', 'Tacos, burritos, churros...');
});
