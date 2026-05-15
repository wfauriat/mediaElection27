import type { ReactNode } from "react";

import { t } from "@/i18n";

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-full flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-baseline justify-between px-4 py-4 md:px-6">
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-slate-900">
              {t.app.title}
            </h1>
            <p className="text-sm text-slate-500">{t.app.subtitle}</p>
          </div>
          <span className="text-xs text-slate-400">v0.1.0</span>
        </div>
      </header>
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 md:px-6">{children}</main>
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 text-xs text-slate-500 md:px-6">
          {t.footer.methodology}{" "}
          <a
            href="https://github.com/wfauriat/mediaElection27"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:underline"
          >
            {t.footer.sourceCode}
          </a>
          .
        </div>
      </footer>
    </div>
  );
}
