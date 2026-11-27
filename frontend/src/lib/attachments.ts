// Pure helpers for Card attachments. The server enforces the same limits (R22);
// these checks only save a round trip.

export const ATTACHMENT_MAX_BYTES = 5 * 1024 * 1024;
export const ATTACHMENT_MAX_COUNT = 5;
export const ATTACHMENT_EXTENSIONS: readonly string[] = [
  "jpg",
  "jpeg",
  "png",
  "webp",
  "pdf",
  "docx",
  "xlsx",
  "pptx",
  "txt",
  "csv",
];

// Value for the file input's `accept` attribute.
export const ATTACHMENT_ACCEPT = ATTACHMENT_EXTENSIONS.map((e) => `.${e}`).join(
  ",",
);

function extensionOf(fileName: string): string {
  const dot = fileName.lastIndexOf(".");
  return dot < 0 ? "" : fileName.slice(dot + 1).toLowerCase();
}

// Returns an error message, or undefined when the file looks acceptable.
export function validateAttachmentFile(file: File): string | undefined {
  if (!ATTACHMENT_EXTENSIONS.includes(extensionOf(file.name))) {
    return `File type not allowed. Allowed types: ${ATTACHMENT_EXTENSIONS.join(", ")}.`;
  }
  if (file.size === 0) return "The file is empty.";
  if (file.size > ATTACHMENT_MAX_BYTES) {
    return `The file is larger than ${ATTACHMENT_MAX_BYTES / (1024 * 1024)} MB.`;
  }
  return undefined;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
