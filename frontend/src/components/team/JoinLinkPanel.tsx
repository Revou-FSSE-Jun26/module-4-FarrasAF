"use client";

import { useState } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseEmptyState from "@/components/shared/BaseEmptyState";
import useToast from "@/hooks/useToast";
import type { TeamJoinLink } from "@/types/api";

interface JoinLinkPanelProps {
  links: TeamJoinLink[];
  onJoinLinkCreate: () => Promise<void>;
  onJoinLinkRevoke: (token: string) => Promise<void>;
}

function statusLabel(link: TeamJoinLink): string {
  if (link.status === "inactive") return "Revoked";
  if (link.isExpired) return "Expired";
  return "Active";
}

export default function JoinLinkPanel({
  links,
  onJoinLinkCreate,
  onJoinLinkRevoke,
}: JoinLinkPanelProps) {
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

  async function copy(link: TeamJoinLink) {
    try {
      await navigator.clipboard.writeText(
        `${window.location.origin}/join/${link.token}`,
      );
      setCopiedId(link.id);
    } catch {
      setCopiedId(null);
      showToast("Could not copy the link.", "error");
    }
  }

  return (
    <section
      aria-labelledby="join-links-heading"
      className="flex flex-col gap-3"
    >
      <div className="flex items-center justify-between">
        <h2 id="join-links-heading" className="text-lg font-semibold">
          Join links
        </h2>
        <BaseButton
          isLoading={isBusy}
          onClick={() => void run(onJoinLinkCreate)}
        >
          Create join link
        </BaseButton>
      </div>
      {links.length === 0 ? (
        <BaseEmptyState message="No join links yet." />
      ) : (
        <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
          {links.map((link) => {
            const isActive = link.status === "active" && !link.isExpired;
            return (
              <li
                key={link.id}
                className="flex flex-col gap-2 px-4 py-2 text-sm lg:flex-row lg:items-center lg:justify-between"
              >
                <span className="text-gray-700">
                  {statusLabel(link)} · expires{" "}
                  {new Date(link.expiresAt).toLocaleDateString()}
                </span>
                {isActive ? (
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
                        void run(() => onJoinLinkRevoke(link.token))
                      }
                    >
                      Revoke
                    </BaseButton>
                  </span>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
