export function suggestionKey(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es").trim();
}

export function matchingSuggestions(options: readonly string[], value: string, multiple = false): string[] {
  const parts = multiple ? value.split(",") : [value];
  const query = suggestionKey(parts[parts.length - 1]);
  const used = new Set(parts.slice(0, -1).map(suggestionKey));
  const seen = new Set<string>();
  return options.filter(option => {
    const key = suggestionKey(option);
    if (seen.has(key) || used.has(key) || !key.includes(query)) return false;
    seen.add(key);
    return true;
  }).sort((a, b) => Number(suggestionKey(b).startsWith(query)) - Number(suggestionKey(a).startsWith(query)));
}

export function applySuggestion(value: string, option: string, multiple = false): string {
  if (!multiple) return option;
  const parts = value.split(",");
  parts[parts.length - 1] = option;
  return parts.map(part => part.trim()).join(", ");
}
