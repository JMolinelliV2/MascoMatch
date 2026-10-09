"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { DragEvent, RefObject } from "react";
import { Icon } from "./pictogram";

type Props = {
  name: string;
  label?: string;
  maxFiles?: number;
  required?: boolean;
  inputRef?: RefObject<HTMLInputElement | null>;
  files?: File[];
  onFilesChange?: (files: File[]) => void;
};

export function PhotoUploader({ name, label = "Foto", maxFiles = 1, required = false, inputRef, files, onFilesChange }: Props) {
  const id = useId();
  const ownRef = useRef<HTMLInputElement>(null);
  const ref = inputRef ?? ownRef;
  const [selected, setSelected] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [dragging, setDragging] = useState(false);
  const [dropError, setDropError] = useState("");
  const currentFiles = files ?? selected;
  const changeRef = useRef(onFilesChange);
  changeRef.current = onFilesChange;

  useEffect(() => {
    const urls = currentFiles.map(file => ["image/jpeg", "image/png", "image/webp"].includes(file.type) && file.size <= 10 * 1024 * 1024 ? URL.createObjectURL(file) : "");
    setPreviews(urls);
    return () => urls.forEach(url => { if (url) URL.revokeObjectURL(url); });
  }, [currentFiles]);

  useEffect(() => {
    const form = ref.current?.form;
    const reset = () => { setSelected([]); setDropError(""); changeRef.current?.([]); };
    form?.addEventListener("reset", reset);
    return () => form?.removeEventListener("reset", reset);
  }, [ref]);

  function changed(next: File[]) {
    setDropError(""); setSelected(next); onFilesChange?.(next);
  }

  function drop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault(); setDragging(false);
    if (!ref.current || ref.current.matches(":disabled")) return;
    const next = Array.from(event.dataTransfer.files);
    if (!next.length) return;
    if (maxFiles === 1 && next.length > 1) { setDropError("Seleccioná una foto por vez."); return; }
    ref.current.files = event.dataTransfer.files;
    changed(next);
  }

  function remove(index: number) {
    const next = currentFiles.filter((_, position) => position !== index);
    if (ref.current) {
      try {
        const transfer = new DataTransfer();
        next.forEach(file => transfer.items.add(file));
        ref.current.files = transfer.files;
      } catch { ref.current.value = ""; }
    }
    changed(next);
  }

  const invalid = currentFiles.length > maxFiles || currentFiles.some(file => file.size > 10 * 1024 * 1024 || !["image/jpeg", "image/png", "image/webp"].includes(file.type));
  return <div className="photo-uploader">
    <div className="field-label">{label} {!required && <span className="optional">(opcional)</span>}</div>
    <label htmlFor={id} className={`photo-dropzone ${dragging ? "photo-dragging" : ""}`} onDragOver={event => { event.preventDefault(); if (!ref.current?.matches(":disabled")) setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={drop}>
      <Icon name="camera" />
      <strong>{maxFiles === 1 ? "Subí una foto" : "Subí fotos del animal"}</strong>
      <span>Arrastrá {maxFiles === 1 ? "la foto" : "las fotos"} acá o hacé clic para elegir</span>
      <span id={`${id}-help`} className="field-help">JPEG, PNG o WebP · Máximo 10 MB{maxFiles > 1 ? ` por foto · Hasta ${maxFiles} fotos` : " · 1 foto"}</span>
      <input id={id} ref={ref} type="file" name={name} multiple={maxFiles > 1} accept="image/jpeg,image/png,image/webp" required={required} className="photo-file-input" aria-label={`${label}${required ? "" : " (opcional)"}`} aria-describedby={`${id}-help`} onChange={event => changed(Array.from(event.target.files || []))} />
    </label>
    {currentFiles.length > 0 && <ul className="photo-thumbnails">{currentFiles.map((file, index) => <li key={`${file.name}-${index}`}>
      {previews[index] ? <img src={previews[index]} alt={`Foto seleccionada ${index + 1}`} /> : <div className="photo-unavailable"><Icon name="camera" /></div>}
      <span className="photo-filename" title={file.name}>{file.name}</span>
      <button type="button" className="photo-remove" aria-label={`Quitar la foto ${index + 1}`} onClick={() => remove(index)}><Icon name="close" /></button>
    </li>)}</ul>}
    {(invalid || dropError) && <p role="alert" className="field-error">{dropError || `Adjuntá hasta ${maxFiles} ${maxFiles === 1 ? "foto" : "fotos"} JPEG, PNG o WebP, de hasta 10 MB cada una.`}</p>}
  </div>;
}
