export const WORKSPACE_SECTIONS = [
  { id: "today", label: "Today" },
  { id: "search", label: "Search" },
  { id: "applications", label: "Applications" },
  { id: "profile", label: "Profile" },
] as const;

export type WorkspaceSection = (typeof WORKSPACE_SECTIONS)[number]["id"];

export const CTA_COPY = {
  analyseCv: "Analyse my CV",
  findJobs: "Find today's jobs",
  showMatches: "Show my best matches",
  save: "Save for later",
  housing: "Compare housing nearby",
} as const;
