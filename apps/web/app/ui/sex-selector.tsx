"use client";
import { useId, useState } from "react";
import { Icon } from "./pictogram";

export function SexSelector() {
  const id = useId();
  const [value, setValue] = useState("unknown");
  const options = [["unknown", "No lo sé"], ["male", "Macho"], ["female", "Hembra"]] as const;
  return <fieldset className="segmented-field">
    <legend className="field-label">Sexo <span className="optional">(opcional)</span></legend>
    <select name="sex" value={value} onChange={event => setValue(event.target.value)} tabIndex={-1} aria-hidden="true" className="sr-only">{options.map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select>
    <div className="segmented-options">{options.map(([key, label]) => <label className="segmented-option" key={key}>
      <input type="radio" name={`sex-choice-${id}`} value={key} checked={value === key} onChange={() => setValue(key)} />
      <span>{value === key && <Icon name="check" />}{label}</span>
    </label>)}</div>
  </fieldset>;
}
