"use client";
import { useState } from "react";
import { breedOptions, colorLabel, colorOptions } from "@/lib/pet-details";
import type { PetDetails } from "@/lib/pet-details";
import { SuggestionField } from "./suggestion-field";

export function ReportTraitFields({ value = {}, species = "", accessories = true, secondaryError = "" }: { value?: PetDetails; species?: string; accessories?: boolean; secondaryError?: string }) {
  const [collar, setCollar] = useState(value.collar_status || "unknown");
  const [clothing, setClothing] = useState(value.clothing_status || "unknown");
  const colorField = (name: string, label: string, current?: string | null) => <SuggestionField name={name} label={label} optional options={colorOptions} maxLength={40} defaultValue={colorLabel(current)} placeholder="Elegí o escribí un color" />;
  return <>
    <SuggestionField name="breed" label="Raza" optional options={breedOptions[species] || [...breedOptions.dog, ...breedOptions.cat]} maxLength={120} defaultValue={value.breed === "unknown" ? "" : value.breed} placeholder="Elegí o escribí una raza" help="Podés indicar mestizo o dejarlo vacío si no lo sabés." />
    {colorField("color", "Color principal", value.primary_color)}
    <SuggestionField name="secondary_colors" label="Otros colores" optional multiple options={colorOptions} error={secondaryError} maxLength={204} defaultValue={value.secondary_colors?.map(colorLabel).join(", ")} placeholder="Ej.: blanco, gris azulado" help="Separá los colores con comas, hasta 5. Podés escribir colores que no estén en las sugerencias." />
    {accessories && <div className="report-accessories">
      <h3>Collar y prendas <span className="optional">(opcional)</span></h3>
      <div className="form-grid">
        <label className="field-label">¿Tiene collar?<select name="collar_status" className="form-input" value={collar} onChange={e => setCollar(e.target.value)}><option value="unknown">No lo sé / no se ve</option><option value="yes">Sí</option><option value="no">No</option></select></label>
        {(collar === "yes" || (collar !== "no" && (value.collar_description || value.collar_color))) && <>{colorField("collar_color", "Color del collar", value.collar_color)}<label className="field-label">Detalles del collar <span className="optional">(opcional)</span><input className="form-input" name="collar_description" maxLength={255} defaultValue={value.collar_description || ""} placeholder="Ej.: collar de tela con chapita" /></label></>}
        <label className="field-label">¿Tiene alguna prenda o accesorio?<select name="clothing_status" className="form-input" value={clothing} onChange={e => setClothing(e.target.value)}><option value="unknown">No lo sé / no se ve</option><option value="yes">Sí</option><option value="no">No</option></select></label>
        {(clothing === "yes" || (clothing !== "no" && (value.clothing_description || value.clothing_color))) && <><label className="field-label">Prenda o accesorio <span className="optional">(opcional)</span><input className="form-input" name="clothing_description" maxLength={120} defaultValue={value.clothing_description || ""} placeholder="Ej.: abrigo, pañuelo o arnés" /></label>{colorField("clothing_color", "Color de la prenda o accesorio", value.clothing_color)}</>}
      </div>
    </div>}
  </>;
}
