import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <div className="text-center py-16">
      <h1 className="text-3xl font-semibold mb-4">Offline Knowledge Assistant</h1>
      <p className="text-slate-600 mb-8 max-w-xl mx-auto">
        Upload internal documentation and ask questions. All processing runs locally —
        no internet required after deployment.
      </p>
      <div className="flex gap-4 justify-center">
        <Link
          to="/documents"
          className="rounded-lg bg-slate-800 px-6 py-3 text-white hover:bg-slate-700"
        >
          Manage Documents
        </Link>
        <Link
          to="/chat"
          className="rounded-lg border border-slate-300 px-6 py-3 text-slate-700 hover:bg-slate-100"
        >
          Start Chat
        </Link>
      </div>
    </div>
  );
}
