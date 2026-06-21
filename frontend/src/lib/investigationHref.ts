export function createInvestigationHref(id: string, query?: string) {
  const search = query ? `?q=${encodeURIComponent(query)}` : "";
  return `/investigation/${id}${search}`;
}
