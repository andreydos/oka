/** Normalize inline list markers from the LLM into readable line breaks. */
function normalizeListFormatting(text: string): string {
  let result = text.trim();
  if (/\s\*\s/.test(result)) {
    result = result.replace(/\s+\*\s+/g, "\n\n• ");
  }
  if (/\s\+\s/.test(result)) {
    result = result.replace(/\s+\+\s+/g, "\n  • ");
  }
  return result;
}

interface Props {
  content: string;
}

export function MessageContent({ content }: Props) {
  return (
    <div className="whitespace-pre-wrap text-left leading-relaxed">{normalizeListFormatting(content)}</div>
  );
}
