import { accessoryLabels, colorLabel } from "@/lib/pet-details";
import type { PetDetails } from "@/lib/pet-details";
export function ReportAccessories({ details }: { details: PetDetails }) {
  const labels = accessoryLabels(details);
  const secondary = details.secondary_colors?.map(colorLabel).filter(Boolean) || [];
  return labels.length || secondary.length ? <div className="accessory-details"><h3>Detalles para reconocerla</h3>{secondary.length > 0 && <p>Otros colores: {secondary.join(", ")}</p>}{labels.map(label => <p key={label}>{label}</p>)}</div> : null;
}
