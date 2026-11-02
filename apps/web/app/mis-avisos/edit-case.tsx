"use client";
import {isSupportedSpecies,speciesOptions} from "@/lib/species";
import { ReportTraitFields } from "../ui/report-trait-fields";
import { readPetDetails, petDetailsError } from "@/lib/pet-details";
import type { PetDetails } from "@/lib/pet-details";
import {useState} from "react";
import type {FormEvent} from "react";
import {LocationPicker} from "../location-picker";
import {localDateTime} from "@/lib/linked-sightings";
import type {Place} from "@/lib/places";
import {editableReportDescription} from "@/lib/report-description";
type Pet=PetDetails & {name:string;species:string;sex:string;primary_color:string;size:string};
export function EditCase({caseId,description,descriptionFormat,lostAt,pet,onSaved,onCancel}:{caseId:string;description:string;descriptionFormat?:string;lostAt:string;pet:Pet;onSaved:()=>void;onCancel:()=>void}){
  const [speciesChoice,setSpeciesChoice]=useState(pet.species);
  const [location,setLocation]=useState<Place|null>(null);const [busy,setBusy]=useState(false);const [error,setError]=useState("");
  async function submit(event:FormEvent<HTMLFormElement>){event.preventDefault();const form=new FormData(event.currentTarget);setError("");const details=readPetDetails(form);if(petDetailsError(details)){setError(petDetailsError(details));return;}setBusy(true);
    const body={pet:{name:form.get("name"),species:form.get("species"),sex:form.get("sex"),size:form.get("size"),...details},case:{description:form.get("description"),lost_at:new Date(String(form.get("date"))).toISOString(),...(location?{latitude:location.latitude,longitude:location.longitude,public_location:location.locality??null,location_accuracy_meters:location.accuracyMeters??null}:{})}};
    try{const response=await fetch(`/api/account/cases/${caseId}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});if(!response.ok)throw new Error("No pudimos guardar tu aviso. Revisá los datos e intentá de nuevo.");onSaved();}catch(cause){setError(cause instanceof Error?cause.message:"No pudimos guardar los cambios.");}finally{setBusy(false);}}
  const field=(name:string,label:string,current:string,options:ReadonlyArray<readonly [string,string]>)=> <label className="field-label">{label}<select onChange={e=>{if(name==="species")setSpeciesChoice(e.target.value);}} className="form-input" name={name} defaultValue={current}>{options.map(([value,text])=><option key={value} value={value}>{text}</option>)}</select></label>;
  if(!isSupportedSpecies(pet.species))return <div className="notice"><p>Este aviso histórico queda fuera del alcance actual de MascoMatch, que admite perros y gatos.</p><button type="button" className="text-button" onClick={onCancel}>Cerrar</button></div>;
  return <form onSubmit={submit} className="section-fields"><fieldset disabled={busy} className="section-fields"><label className="field-label">Nombre<input name="name" className="form-input" required maxLength={120} defaultValue={pet.name}/></label>
    {field("species","Mascota",pet.species,speciesOptions)}
    {field("sex","Sexo",pet.sex,[["unknown","No sé"],["male","Macho"],["female","Hembra"]])}
    <ReportTraitFields value={pet} species={speciesChoice}/>
    {field("size","Tamaño",pet.size,[["unknown","No sé"],["tiny","Muy pequeño"],["small","Pequeño"],["medium","Mediano"],["large","Grande"]])}
    <label className="field-label">Última vez que lo viste<input className="form-input" name="date" type="datetime-local" defaultValue={localDateTime(new Date(lostAt))} required/></label>
    <label className="field-label">Descripción<textarea name="description" className="form-input" defaultValue={editableReportDescription(description,descriptionFormat)} placeholder="Ej.: tiene una mancha blanca en el pecho, una oreja caída y un collar azul." maxLength={4000}/></label>
    <h3>Cambiar el lugar</h3><p className="field-help">Si no elegís otro lugar, conservamos la ubicación del aviso.</p><LocationPicker value={location} onChange={setLocation} lost/>
    <div className="location-actions"><button className="button button-primary" type="submit">{busy?"Guardando…":"Guardar cambios"}</button><button className="text-button" type="button" onClick={onCancel}>Cancelar</button></div></fieldset>{error&&<p className="notice notice-warning" role="alert">{error}</p>}</form>;
}
