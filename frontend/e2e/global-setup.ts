import type { FullConfig } from "@playwright/test";

// `next dev` compiles each route on its first request. When parallel workers
// hit several uncompiled routes at once, navigations and proxied /api calls
// stall past the test timeouts. Requesting every route once up front (as a
// document and as a client-navigation RSC payload) compiles them before any
// test runs. Dynamic segments use a placeholder id; the pages are client
// components, so no data or session is needed to compile them.
const PLACEHOLDER_ID = "00000000-0000-0000-0000-000000000000";

const ROUTES: readonly string[] = [
  "/",
  "/login",
  "/register",
  "/boards",
  `/boards/${PLACEHOLDER_ID}`,
  `/boards/${PLACEHOLDER_ID}/activity`,
  `/boards/${PLACEHOLDER_ID}/analytics`,
  `/boards/${PLACEHOLDER_ID}/settings`,
  "/teams",
  `/teams/${PLACEHOLDER_ID}`,
  `/join/${PLACEHOLDER_ID}`,
  `/invite/${PLACEHOLDER_ID}`,
  "/profile",
  "/search",
];

export default async function globalSetup(config: FullConfig): Promise<void> {
  const baseURL = config.projects[0]?.use.baseURL;
  if (!baseURL) return;
  // Sequential on purpose: one compile at a time is fastest for the dev server.
  for (const route of ROUTES) {
    const url = new URL(route, baseURL);
    await fetch(url, { redirect: "manual" });
    await fetch(url, { headers: { RSC: "1" }, redirect: "manual" });
  }
}
