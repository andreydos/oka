import type { Citation } from "../types";
import { api } from "../api/client";

interface Props {
  citations: Citation[];
}

export function CitationList({ citations }: Props) {
  if (!citations.length) return null;

  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Sources</p>
      {citations.map((c) => (
        <div
          key={c.chunk_id}
          className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm"
        >
          <div className="font-medium text-slate-800">
            <a
              href={api.documentFileUrl(c.document_id, c.page)}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-700 hover:underline"
            >
              {c.document_name}
            </a>
            {c.section && (
              <span className="ml-2 text-slate-600">— {c.section}</span>
            )}
            {c.page != null && (
              <span className="ml-2 text-slate-500">p. {c.page}</span>
            )}
          </div>
          <p className="mt-1 text-slate-600 italic">&ldquo;{c.quote}&rdquo;</p>
        </div>
      ))}
    </div>
  );
}
