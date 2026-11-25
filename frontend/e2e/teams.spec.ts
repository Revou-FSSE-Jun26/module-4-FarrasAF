import {
  createTeam,
  createTeamJoinLink,
  expect,
  joinTeam,
  loginInBrowser,
  test,
  uniqueId,
} from "./fixtures";

const INVALID_LINK_MESSAGE = "This join link is not valid.";

test.describe("teams and join links", () => {
  test("creates a Team and shows it in the list", async ({
    page,
    context,
    makeUser,
  }) => {
    const owner = await makeUser("Team Owner");
    await loginInBrowser(context, owner);
    const teamName = `Team ${uniqueId()}`;

    await page.goto("/teams");
    await page.getByLabel("Team name").fill(teamName);
    await page.getByRole("button", { name: "Create Team" }).click();

    const row = page.getByRole("link", { name: new RegExp(teamName) });
    await expect(row).toBeVisible();
    await expect(row).toContainText("Team admin");
  });

  test("Team admin generates a join link, a second user previews and accepts it", async ({
    page,
    context,
    browser,
    baseURL,
    makeUser,
  }) => {
    const owner = await makeUser("Link Owner");
    const joiner = await makeUser("Link Joiner");
    const team = await createTeam(owner);
    await loginInBrowser(context, owner);

    await page.goto(`/teams/${team.id}`);
    await expect(page.getByText("No join links yet.")).toBeVisible();
    await page.getByRole("button", { name: "Create join link" }).click();
    await expect(page.getByText(/^Active/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Copy link" })).toBeVisible();

    const links = await owner.api.get(`/api/teams/${team.id}/join-links`);
    expect(links.ok()).toBe(true);
    const body = (await links.json()) as { items: Array<{ token: string }> };
    expect(body.items).toHaveLength(1);
    const token = body.items[0].token;

    const joinerContext = await browser.newContext({ baseURL });
    try {
      await loginInBrowser(joinerContext, joiner);
      const joinerPage = await joinerContext.newPage();
      await joinerPage.goto(`/join/${token}`);
      await expect(
        joinerPage.getByRole("heading", { name: `Join ${team.name}?` }),
      ).toBeVisible();
      await joinerPage.getByRole("button", { name: "Join Team" }).click();

      await expect(joinerPage).toHaveURL(new RegExp(`/teams/${team.id}`));
      await expect(
        joinerPage.getByRole("heading", { name: team.name }),
      ).toBeVisible();
      await expect(
        joinerPage.getByRole("list").getByText("Link Joiner"),
      ).toBeVisible();
    } finally {
      await joinerContext.close();
    }
  });

  test("shows a generic message for an unknown link", async ({
    page,
    context,
    makeUser,
  }) => {
    const user = await makeUser();
    await loginInBrowser(context, user);

    await page.goto(`/join/unknown-token-${uniqueId()}`);

    await expect(page.getByText(INVALID_LINK_MESSAGE)).toBeVisible();
    await expect(page.getByRole("button", { name: "Join Team" })).toHaveCount(
      0,
    );
  });

  test("shows the same message for a revoked link and the admin sees it as revoked", async ({
    page,
    context,
    makeUser,
  }) => {
    const owner = await makeUser("Revoker");
    const joiner = await makeUser("Late Joiner");
    const team = await createTeam(owner);
    const link = await createTeamJoinLink(owner, team.id);

    await loginInBrowser(context, owner);
    await page.goto(`/teams/${team.id}`);
    await page.getByRole("button", { name: "Revoke" }).click();
    await expect(page.getByText(/^Revoked/)).toBeVisible();

    const joinerPage = await context.newPage();
    await context.clearCookies();
    await loginInBrowser(context, joiner);
    await joinerPage.goto(`/join/${link.token}`);
    await expect(joinerPage.getByText(INVALID_LINK_MESSAGE)).toBeVisible();
  });

  test("regular members do not see join link controls", async ({
    page,
    context,
    makeUser,
  }) => {
    const owner = await makeUser("Admin Person");
    const member = await makeUser("Regular Person");
    const team = await createTeam(owner);
    const link = await createTeamJoinLink(owner, team.id);
    await joinTeam(member, link.token);
    await loginInBrowser(context, member);

    await page.goto(`/teams/${team.id}`);

    await expect(page.getByRole("heading", { name: team.name })).toBeVisible();
    await expect(page.getByText("Admin Person")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Join links" })).toHaveCount(
      0,
    );
    await expect(
      page.getByRole("button", { name: "Create join link" }),
    ).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Revoke" })).toHaveCount(0);
  });
});
