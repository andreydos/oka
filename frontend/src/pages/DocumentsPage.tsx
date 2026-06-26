import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Document, DocumentStatus } from "../types";

const ACCEPT = ".pdf,.docx,.txt,.md,.html,.htm,.png,.jpg,.jpeg,.webp";

const ALLOWED_EXTENSIONS = new Set([
  ".pdf",
  ".docx",
  ".txt",
  ".md",
  ".markdown",
  ".html",
  ".htm",
  ".png",
  ".jpg",
  ".jpeg",
  ".webp",
]);

const ALLOWED_IMAGE_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);

function isSupportedFile(file: File): boolean {
  const name = file.name.toLowerCase();
  const ext = name.includes(".") ? name.slice(name.lastIndexOf(".")) : "";
  if (file.type.startsWith("image/")) {
    return ALLOWED_IMAGE_TYPES.has(file.type);
  }
  return ALLOWED_EXTENSIONS.has(ext);
}

function filterSupportedFiles(files: FileList | File[]): File[] {
  const selected = Array.from(files);
  const supported = selected.filter(isSupportedFile);
  const rejected = selected.length - supported.length;
  if (rejected > 0) {
    throw new Error(
      "Unsupported file type. Upload PDF, DOCX, TXT, Markdown, HTML, or images (PNG, JPEG, WebP)."
    );
  }
  return supported;
}

const statusColors: Record<DocumentStatus, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  processing: "bg-blue-100 text-blue-800",
  indexed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  archived: "bg-slate-100 text-slate-600",
};

export function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    try {
      setDocuments(await api.listDocuments());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  const handleUpload = async (files: FileList | null) => {
    if (!files?.length) return;
    setUploading(true);
    setError(null);
    try {
      for (const file of filterSupportedFiles(files)) {
        await api.uploadDocument(file);
      }
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this document and its indexed content?")) return;
    await api.deleteDocument(id);
    await load();
  };

  const handleReindex = async (id: string) => {
    await api.reindexDocument(id);
    await load();
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Documents</h1>
        <label className="cursor-pointer rounded-lg bg-slate-800 px-4 py-2 text-sm text-white hover:bg-slate-700">
          {uploading ? "Uploading…" : "Upload files"}
          <input
            ref={fileRef}
            type="file"
            multiple
            accept={ACCEPT}
            className="hidden"
            disabled={uploading}
            onChange={(e) => handleUpload(e.target.files)}
          />
        </label>
      </div>

      <div
        className="mb-6 rounded-xl border-2 border-dashed border-slate-300 p-8 text-center text-slate-500"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleUpload(e.dataTransfer.files);
        }}
      >
        Drop PDF, DOCX, TXT, Markdown, HTML, or images (PNG, JPEG, WebP) here.
        <p className="mt-2 text-xs text-slate-400">
          Images are processed with offline OCR. English text only — other languages may be inaccurate.
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div>
      )}

      {loading ? (
        <p className="text-slate-500">Loading…</p>
      ) : documents.length === 0 ? (
        <p className="text-slate-500">No documents yet. Upload internal documentation to get started.</p>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr>
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Version</th>
                <th className="px-4 py-3 font-medium">Chunks</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-t border-slate-100">
                  <td className="px-4 py-3">
                    <div className="font-medium">{doc.title}</div>
                    <div className="text-slate-500">{doc.filename}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[doc.status]}`}
                    >
                      {doc.status}
                      {(doc.status === "pending" || doc.status === "processing") && " …"}
                    </span>
                  </td>
                  <td className="px-4 py-3">{doc.version}</td>
                  <td className="px-4 py-3">{doc.chunk_count}</td>
                  <td className="px-4 py-3 space-x-2">
                    <button
                      type="button"
                      onClick={() => handleReindex(doc.id)}
                      className="text-slate-600 hover:text-slate-900"
                    >
                      Reindex
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(doc.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
