"use client";

import { useState } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseEmptyState from "@/components/shared/BaseEmptyState";
import useToast from "@/hooks/useToast";
import type { InvitationLink } from "@/types/api";

interface InvitationLinkPanelProps {
  links: InvitationLink[];
  onInvitationCreate: () => Promise<void>;
  onInvitationRevoke: (token: string) => Promise<void>;
}

export default function InvitationLinkPanel({
  links,
  onInvitationCreate,
  onInvitationRevoke,
}: InvitationLinkPanelProps) {
  const { showToast } = useToast();
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  async function run(action: () => Promise<void>) {
    setIsBusy(true);
    try {
      await action();
    } finally {
      setIsBusy(false);
    }
  }

  async function copy(link: InvitationLink) {
    try {
      await navigator.clipboard.writeText(
        `${window.location.origin}/invite/${link.token}`,
      );
      setCopiedId(link.id);
    } catch {
      setCopiedId(null);
      showToast("Could not copy the link.", "error");
    }
  }

  return (
    <section
      aria-labelledby="invitations-heading"
      className="flex flex-col gap-3"
    >
      <div className="flex items-center justify-between">
        <h2 id="invitations-heading" className="text-lg font-semibold">
          Invitation links
        </h2>
        <BaseButton
          isLoading={isBusy}
          onClick={() => void run(onInvitationCreate)}
        >
          Create invitation link
        </BaseButton>
      </div>
      <p className="text-sm text-gray-600">
        Anyone with an active link can view this Board read-only, without an
        account.
      </p>
      {links.length === 0 ? (
        <BaseEmptyState message="No invitation links yet." />
      ) : (
        <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
          {links.map((link) => (
            <li
              key={link.id}
              className="flex flex-col gap-2 px-4 py-2 text-sm lg:flex-row lg:items-center lg:justify-between"
            >
              <span className="text-gray-700">
                {link.status === "active" ? "Active" : "Revoked"} · created{" "}
                {new Date(link.createdAt).toLocaleDateString()}
              </span>
              {link.status === "active" ? (
                <span className="flex gap-2">
                  <BaseButton
                    variant="secondary"
                    onClick={() => void copy(link)}
                  >
                    {copiedId === link.id ? "Copied" : "Copy link"}
                  </BaseButton>
                  <BaseButton
                    variant="danger"
                    isLoading={isBusy}
                    onClick={() =>
                      void run(() => onInvitationRevoke(link.token))
                    }
                  >
                    Revoke
                  </BaseButton>
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
