"use client";
import { useEffect, useId, useRef } from "react";
import { Icon } from "./pictogram";

export function SavedChangesDialog({ description, onClose }: { description: string; onClose: () => void }) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descriptionId = useId();
  const backdropPressed = useRef(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    if (!dialog.open) dialog.showModal();
    return () => { document.body.style.overflow = previousOverflow; };
  }, []);

  return <dialog ref={dialogRef} className="saved-changes-dialog" aria-labelledby={titleId} aria-describedby={descriptionId}
    onClose={onClose}
    onPointerDown={event => {
      const bounds = event.currentTarget.getBoundingClientRect();
      backdropPressed.current = event.target === event.currentTarget &&
        (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom);
    }}
    onClick={event => { if (backdropPressed.current && event.target === event.currentTarget) event.currentTarget.close(); backdropPressed.current = false; }}>
    <button type="button" className="saved-changes-close" aria-label="Cerrar confirmación" onClick={() => dialogRef.current?.close()}><Icon name="close" /></button>
    <span className="saved-changes-mark" aria-hidden="true"><Icon name="check" /></span>
    <h2 id={titleId}>Cambios guardados</h2>
    <p id={descriptionId}>{description}</p>
    <form method="dialog"><button type="submit" className="button button-primary" autoFocus>Entendido</button></form>
  </dialog>;
}
