"use client";

import { useState } from "react";
import BaseButton from "@/components/shared/BaseButton";
import BaseEmptyState from "@/components/shared/BaseEmptyState";
import type { BoardMember, BoardRole, TeamMember } from "@/types/api";

interface BoardMemberPanelProps {
  members: BoardMember[];
  addableMembers: TeamMember[];
  isAdmin: boolean;
  onMemberAdd: (userId: string, role: BoardRole) => Promise<void>;
  onMemberRoleChange: (userId: string, role: BoardRole) => Promise<void>;
  onMemberRemove: (userId: string) => Promise<void>;
}

function toRole(value: string): BoardRole {
  return value === "admin" ? "admin" : "member";
}

export default function BoardMemberPanel({
  members,
  addableMembers,
  isAdmin,
  onMemberAdd,
  onMemberRoleChange,
  onMemberRemove,
}: BoardMemberPanelProps) {
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const [newUserId, setNewUserId] = useState<string>("");
  const [newRole, setNewRole] = useState<BoardRole>("member");

  const selectedUserId = newUserId || addableMembers[0]?.userId || "";

  async function run(action: () => Promise<void>) {
    setIsBusy(true);
    try {
      await action();
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section aria-labelledby="members-heading" className="flex flex-col gap-3">
      <h2 id="members-heading" className="text-lg font-semibold">
        Members
      </h2>
      {members.length === 0 ? (
        <BaseEmptyState message="No members." />
      ) : (
        <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
          {members.map((member) => (
            <li
              key={member.userId}
              className="flex flex-col gap-2 px-4 py-2 text-sm lg:flex-row lg:items-center lg:justify-between"
            >
              <span className="text-gray-900">{member.displayName}</span>
              {isAdmin ? (
                <span className="flex items-center gap-2">
                  <select
                    aria-label={`Role of ${member.displayName}`}
                    value={member.role}
                    disabled={isBusy}
                    onChange={(e) =>
                      void run(() =>
                        onMemberRoleChange(
                          member.userId,
                          toRole(e.target.value),
                        ),
                      )
                    }
                    className="min-h-10 rounded-md border border-gray-300 px-2 text-sm"
                  >
                    <option value="admin">Admin</option>
                    <option value="member">Member</option>
                  </select>
                  {member.role === "member" ? (
                    <BaseButton
                      variant="danger"
                      isLoading={isBusy}
                      aria-label={`Remove ${member.displayName}`}
                      onClick={() =>
                        void run(() => onMemberRemove(member.userId))
                      }
                    >
                      Remove
                    </BaseButton>
                  ) : null}
                </span>
              ) : (
                <span className="text-gray-600">
                  {member.role === "admin" ? "Admin" : "Member"}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}
      {isAdmin ? (
        addableMembers.length === 0 ? (
          <p className="text-sm text-gray-600">
            All Team members are already on this Board.
          </p>
        ) : (
          <div className="flex flex-col gap-2 lg:flex-row lg:items-end">
            <div className="flex w-full flex-col gap-1">
              <label
                htmlFor="add-member-user"
                className="text-sm font-medium text-gray-900"
              >
                Team member
              </label>
              <select
                id="add-member-user"
                value={selectedUserId}
                onChange={(e) => setNewUserId(e.target.value)}
                className="min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                {addableMembers.map((member) => (
                  <option key={member.userId} value={member.userId}>
                    {member.displayName}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex w-full flex-col gap-1">
              <label
                htmlFor="add-member-role"
                className="text-sm font-medium text-gray-900"
              >
                Role
              </label>
              <select
                id="add-member-role"
                value={newRole}
                onChange={(e) => setNewRole(toRole(e.target.value))}
                className="min-h-10 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <BaseButton
              isLoading={isBusy}
              onClick={() =>
                void run(async () => {
                  await onMemberAdd(selectedUserId, newRole);
                  setNewUserId("");
                })
              }
            >
              Add member
            </BaseButton>
          </div>
        )
      ) : null}
    </section>
  );
}
