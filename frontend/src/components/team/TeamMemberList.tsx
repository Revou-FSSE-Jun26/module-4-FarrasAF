import BaseEmptyState from "@/components/shared/BaseEmptyState";
import type { TeamMember } from "@/types/api";

interface TeamMemberListProps {
  members: TeamMember[];
}

export default function TeamMemberList({ members }: TeamMemberListProps) {
  if (members.length === 0) {
    return <BaseEmptyState message="No members yet." />;
  }
  return (
    <ul className="divide-y divide-gray-200 rounded-lg border border-gray-200 bg-white">
      {members.map((member) => (
        <li
          key={member.userId}
          className="flex items-center justify-between px-4 py-2 text-sm"
        >
          <span className="text-gray-900">{member.displayName}</span>
          <span className="text-gray-600">
            {member.teamRole === "team_admin" ? "Team admin" : "Member"}
          </span>
        </li>
      ))}
    </ul>
  );
}
