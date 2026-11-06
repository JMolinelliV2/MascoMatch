import { dogTraits } from "@/lib/lost-dogs";
import type { PetDetails } from "@/lib/pet-details";
import { ReportAccessories } from "./report-accessories";

export type FoundPetDetailsData = PetDetails & { sex?: string; size?: string };

export function FoundPetDetails({ details = {} }: { details?: FoundPetDetailsData }) {
  const labels = dogTraits({ breed: details.breed || "unknown", sex: details.sex || "unknown", size: details.size || "unknown", primary_color: details.primary_color || "unknown" });
  return <>{labels.length > 0 && <p className="dog-traits">{labels.join(" · ")}</p>}<ReportAccessories details={details} /></>;
}
