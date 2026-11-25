"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";
import { supportShareText, supportShareUrl } from "@/lib/match-support";
import type { MatchSupportKind } from "@/lib/match-support";
import { Icon } from "./pictogram";
import "./match-support.css";

const shareMessage = `${supportShareText}\n\n${supportShareUrl}`;

const introduction = {
  sighting: "Gracias por confirmar el avistamiento. Cada pista ayuda a tu búsqueda. Si querés, también podés ayudar a otras familias.",
  contact: "Mientras coordinás el reencuentro, podés ayudar a que otras familias conozcan MascoMatch.",
  recovered: "Gracias por cerrar la búsqueda. Podés ayudar a que otras familias tengan más oportunidades de reencontrarse con sus mascotas.",
};

export function MatchSupport({ kind, petName, onClose }: { kind: MatchSupportKind; petName?: string; onClose: () => void }) {
  const titleId = useId();
  const descriptionId = useId();
  const dialog = useRef<HTMLDialogElement>(null);
  const shareRef = useRef<HTMLTextAreaElement>(null);
  const [showShare, setShowShare] = useState(false);
  const [copied, setCopied] = useState(false);
  const inline = kind === "contact";

  useEffect(() => {
    const element = dialog.current;
    if (!element || element.open) return;
    element.showModal();
    return () => element.close();
  }, []);

  useEffect(() => { if (showShare) shareRef.current?.focus(); }, [showShare]);

  async function share() {
    if (navigator.share) {
      try {
        await navigator.share({ title: "MascoMatch", text: supportShareText, url: supportShareUrl });
        return;
      } catch (cause) {
        if (cause instanceof Error && cause.name === "AbortError") return;
      }
    }
    setShowShare(true);
  }

  async function copyMessage() {
    try {
      await navigator.clipboard.writeText(shareMessage);
      setCopied(true);
    } catch {
      shareRef.current?.focus();
      shareRef.current?.select();
    }
  }

  function dismiss() {
    if (dialog.current?.open) dialog.current.close();
    else onClose();
  }

  const content = <>
    <header className="match-support-header">
      <span className="match-support-mark"><Icon name={kind === "recovered" ? "heart" : "paw"} /></span>
      <h2 id={titleId}>{kind === "recovered" ? petName ? `¡${petName} volvió a casa!` : "¡Tu mascota volvió a casa!" : "Ayudá a que más mascotas vuelvan a casa"}</h2>
      <p id={descriptionId}>{introduction[kind]}</p>
    </header>
    <div className="match-support-options">
      <Link href="/apoyanos" className="match-support-option match-support-donate">
        <span className="match-support-option-icon"><Icon name="heart" /></span>
        <span><strong>Hacer una donación</strong><small>Tu aporte ayuda a sostener las alertas, el mapa y las fotos de los avisos.</small></span>
        <Icon name="arrow" />
      </Link>
      <button type="button" className="match-support-option match-support-share" onClick={() => void share()}>
        <span className="match-support-option-icon"><Icon name="share" /></span>
        <span><strong>Compartir MascoMatch</strong><small>Difundí el enlace en tus redes o con tu comunidad.</small></span>
        <Icon name="arrow" />
      </button>
    </div>
    {showShare && <div className="match-support-share-message">
      <label className="field-label" htmlFor={`${titleId}-message`}>Mensaje listo para compartir</label>
      <textarea id={`${titleId}-message`} ref={shareRef} className="form-input" value={shareMessage} readOnly rows={4} />
      <div className="match-support-share-actions">
        <button type="button" className="text-button" onClick={() => void copyMessage()}><Icon name="copy" /> Copiar mensaje</button>
        <a className="text-button" href={`https://wa.me/?text=${encodeURIComponent(shareMessage)}`} target="_blank" rel="noreferrer">Abrir WhatsApp</a>
      </div>
      {copied && <p className="field-help" role="status">Mensaje copiado. Pegalo en la red que prefieras.</p>}
    </div>}
    <button className="text-button match-support-dismiss" type="button" autoFocus={!inline} onClick={dismiss}>Por ahora no</button>
  </>;

  return inline
    ? <aside className="match-support match-support-inline" aria-labelledby={titleId} aria-describedby={descriptionId}>{content}</aside>
    : <dialog ref={dialog} className="match-support match-support-dialog" aria-labelledby={titleId} aria-describedby={descriptionId} onClose={event => { if (!event.currentTarget.open) onClose(); }}>{content}</dialog>;
}
