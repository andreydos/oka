import { Link, Outlet } from "react-router-dom";
import { HealthIndicator } from "./HealthIndicator";

export function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-xl font-semibold text-slate-800">
              OKA
            </Link>
            <nav className="flex gap-4 text-sm">
              <Link to="/documents" className="text-slate-600 hover:text-slate-900">
                Documents
              </Link>
              <Link to="/chat" className="text-slate-600 hover:text-slate-900">
                Chat
              </Link>
            </nav>
          </div>
          <HealthIndicator />
        </div>
      </header>
      <main className="flex-1 mx-auto w-full max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
