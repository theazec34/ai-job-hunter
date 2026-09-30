"use client";

import { BriefcaseBusiness, Search, Sparkles, UserRound } from "lucide-react";

import { WORKSPACE_SECTIONS, WorkspaceSection } from "@/lib/ui-copy";

const icons = {
  today: Sparkles,
  search: Search,
  applications: BriefcaseBusiness,
  profile: UserRound,
};

type WorkspaceNavigationProps = {
  active: WorkspaceSection;
  onChange: (section: WorkspaceSection) => void;
};

export function WorkspaceNavigation({ active, onChange }: WorkspaceNavigationProps) {
  return (
    <>
      <nav aria-label="Workspace" className="hidden w-52 shrink-0 md:block">
        <div className="sticky top-6 space-y-1">
          {WORKSPACE_SECTIONS.map((section) => {
            const Icon = icons[section.id];
            const selected = section.id === active;
            return (
              <button
                type="button"
                key={section.id}
                aria-current={selected ? "page" : undefined}
                className={`flex min-h-11 w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm font-semibold transition-colors ${
                  selected
                    ? "bg-cyan-800 text-white"
                    : "text-slate-600 hover:bg-white hover:text-slate-950"
                }`}
                onClick={() => onChange(section.id)}
              >
                <Icon aria-hidden="true" className="size-5" />
                {section.label}
              </button>
            );
          })}
        </div>
      </nav>

      <nav
        aria-label="Workspace"
        className="fixed inset-x-0 bottom-0 z-50 grid grid-cols-4 border-t border-slate-200 bg-white/95 px-1 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"
      >
        {WORKSPACE_SECTIONS.map((section) => {
          const Icon = icons[section.id];
          const selected = section.id === active;
          return (
            <button
              type="button"
              key={section.id}
              aria-current={selected ? "page" : undefined}
              className={`flex min-h-16 flex-col items-center justify-center gap-1 px-1 text-xs font-semibold ${
                selected ? "text-cyan-800" : "text-slate-600"
              }`}
              onClick={() => onChange(section.id)}
            >
              <Icon aria-hidden="true" className="size-5" />
              {section.label}
            </button>
          );
        })}
      </nav>
    </>
  );
}
