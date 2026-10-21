import { test, expect } from "@playwright/test";

test("user can log in", async ({ page }) => {
  await page.goto("/login");
  await page.fill("#email", "qa@example.com");
  await page.fill("#password", "hunter2");
  await page.click("form > div:nth-child(3) > button");
  await page.waitForTimeout(3000);
  expect(await page.isVisible(".css-1x9fz2k")).toBe(true);
});

test("cart shows added product", async ({ page }) => {
  await page.goto("/login");
  await page.fill("#email", "qa@example.com");
  await page.fill("#password", "hunter2");
  await page.click("form > div:nth-child(3) > button");
  await page.waitForTimeout(3000);
  await page.goto("/products/42");
  await page.getByRole("button", { name: "Add to cart" }).click();
  await page.goto("/cart");
  await expect(page.getByRole("row", { name: /Blue mug/ })).toBeVisible();
});

test("checkout places the order", async ({ page }) => {
  await page.goto("/cart");
  await page.getByRole("button", { name: "Checkout" }).click();
  await expect(page.getByText("Order confirmed")).toBeVisible();
});

test("loyalty discounts", async ({ page }) => {
  for (const [years, price] of [[0, "$20.00"], [2, "$18.00"], [5, "$17.00"]]) {
    await page.goto(`/debug/pricing?loyaltyYears=${years}&product=42`);
    await expect(page.getByTestId("price")).toHaveText(price as string);
  }
});

test("guest can buy a mug end to end", async ({ page }) => {
  await page.goto("/products/42");
  await page.getByRole("button", { name: "Add to cart" }).click();
  await page.getByRole("link", { name: "Cart" }).click();
  await page.getByRole("button", { name: "Checkout as guest" }).click();
  await page.getByLabel("Email").fill(`guest-${Date.now()}@example.test`);
  await page.getByLabel("Card number").fill("4242 4242 4242 4242");
  await page.getByRole("button", { name: "Pay" }).click();
  await expect(page.getByText("Order confirmed")).toBeVisible();
  await expect(page.getByTestId("order-total")).toHaveText("$20.00");
});
