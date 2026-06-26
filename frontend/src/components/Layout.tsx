import { Link, Outlet } from "react-router-dom";
import { HealthIndicator } from "./HealthIndicator";

export function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-3 py-3 md:px-4 md:py-4 flex items-center justify-between gap-2">
          <div className="flex items-center gap-4 md:gap-8 min-w-0">
            <Link to="/" className="text-lg md:text-xl font-semibold text-slate-800 shrink-0">
              OKA
            </Link>
            <nav className="flex gap-3 md:gap-4 text-sm shrink-0">
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
      <main className="flex-1 mx-auto w-full max-w-6xl px-3 py-4 md:px-4 md:py-8 min-h-0">
        <Outlet />
      </main>
    </div>
  );
}
