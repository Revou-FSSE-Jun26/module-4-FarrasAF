import type { ActivityEntry } from "@/types/api";

function quoted(value: string | undefined): string {
  return value ? ` "${value}"` : "";
}

// The sentence for one Activity entry, for example
// `Ada moved the card "Fix login" from "To Do" to "Doing"`. Entries recorded
// before details existed have no names, so they get a shorter sentence.
export function describeActivity(entry: ActivityEntry): string {
  const who = entry.actor.displayName;
  const d = entry.details ?? {};
  switch (entry.eventType) {
    case "card_created":
      return d.columnName
        ? `${who} created the card${quoted(d.cardTitle)} in "${d.columnName}"`
        : `${who} created a card${quoted(d.cardTitle)}`;
    case "card_updated":
      return `${who} updated the card${quoted(d.cardTitle)}`;
    case "card_moved":
      if (d.fromColumnName && d.toColumnName) {
        return d.fromColumnName === d.toColumnName
          ? `${who} reordered the card${quoted(d.cardTitle)} in "${d.fromColumnName}"`
          : `${who} moved the card${quoted(d.cardTitle)} from "${d.fromColumnName}" to "${d.toColumnName}"`;
      }
      return `${who} moved the card${quoted(d.cardTitle)}`;
    case "card_deleted":
      return `${who} deleted the card${quoted(d.cardTitle)}`;
    case "comment_created":
      return `${who} commented on the card${quoted(d.cardTitle)}`;
    case "comment_edited":
      return `${who} edited a comment on the card${quoted(d.cardTitle)}`;
    case "comment_deleted":
      return `${who} deleted a comment on the card${quoted(d.cardTitle)}`;
    case "column_created":
      return `${who} created the column${quoted(d.columnName)}`;
    case "column_deleted":
      return `${who} deleted the column${quoted(d.columnName)}`;
    case "member_joined":
      return d.memberName
        ? `${who} added ${d.memberName} to the board`
        : `${who} added a member to the board`;
    case "member_removed":
      return d.memberName
        ? `${who} removed ${d.memberName} from the board`
        : `${who} removed a member from the board`;
  }
}
