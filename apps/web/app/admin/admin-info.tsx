"use client";

import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Icon } from "../ui/pictogram";
import { adminHelp } from "./admin-help";

const OPEN_EVENT = "mascomatch:admin-info";

export function AdminInfo({ label, help }: { label: string; help: string }) {
  const id = useId();
  const trigger = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const focused = useRef(false);
  const pinned = useRef(false);
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<{ left: number; top: number } | null>(null);

  function cancelClose() { if (closeTimer.current) clearTimeout(closeTimer.current); closeTimer.current = null; }
  function close() { cancelClose(); pinned.current = false; setOpen(false); setPosition(null); }
  function show() { cancelClose(); window.dispatchEvent(new CustomEvent(OPEN_EVENT, { detail: id })); setOpen(true); }
  function leave() { if (!pinned.current && !focused.current) { cancelClose(); closeTimer.current = setTimeout(close, 150); } }

  function reposition() {
    if (!trigger.current || !panel.current) return;
    const anchor = trigger.current.getBoundingClientRect();
    const box = panel.current.getBoundingClientRect();
    const viewWidth = document.documentElement.clientWidth;
    const viewHeight = document.documentElement.clientHeight;
    if (anchor.bottom <= 0 || anchor.top >= viewHeight || anchor.right <= 0 || anchor.left >= viewWidth) { close(); return; }
    const left = Math.max(12, Math.min(viewWidth - box.width - 12, anchor.left + anchor.width / 2 - box.width / 2));
    const below = anchor.bottom + 10;
    const top = below + box.height <= viewHeight - 12 ? below : Math.max(12, anchor.top - box.height - 10);
    setPosition({ left, top });
  }

  useEffect(() => () => cancelClose(), []);
  useLayoutEffect(() => { if (open) reposition(); }, [open, help, label]);

  useEffect(() => {
    if (!open) return;
    function outside(event: PointerEvent) { if (!trigger.current?.contains(event.target as Node) && !panel.current?.contains(event.target as Node)) close(); }
    function key(event: KeyboardEvent) { if (event.key === "Escape") { event.preventDefault(); event.stopPropagation(); close(); } }
    function other(event: Event) { if ((event as CustomEvent).detail !== id) close(); }
    function scroll(event: Event) { if (!panel.current?.contains(event.target as Node)) reposition(); }
    document.addEventListener("pointerdown", outside, true);
    document.addEventListener("keydown", key, true);
    document.addEventListener("scroll", scroll, true);
    window.addEventListener("resize", reposition);
    window.addEventListener(OPEN_EVENT, other);
    return () => {
      document.removeEventListener("pointerdown", outside, true);
      document.removeEventListener("keydown", key, true);
      document.removeEventListener("scroll", scroll, true);
      window.removeEventListener("resize", reposition);
      window.removeEventListener(OPEN_EVENT, other);
    };
  }, [open, id]);

  return <>
    <button ref={trigger} type="button" className="admin-info-trigger" aria-label={`Información sobre ${label}`} aria-expanded={open} aria-controls={open ? id : undefined} aria-describedby={open ? id : undefined}
      onPointerEnter={event => { if (event.pointerType === "mouse") show(); }} onPointerLeave={leave}
      onFocus={() => { focused.current = true; show(); }} onBlur={() => { focused.current = false; close(); }}
      onClick={event => { event.stopPropagation(); if (pinned.current) close(); else { pinned.current = true; show(); } }}><Icon name="info" /></button>
    {open && createPortal(<div ref={panel} id={id} role="tooltip" className="admin-info-popover" style={{ left: position?.left ?? 0, top: position?.top ?? 0, visibility: position ? "visible" : "hidden" }} onPointerEnter={cancelClose} onPointerLeave={leave}><strong>{label}</strong><p>{help}</p></div>, document.body)}
  </>;
}

export function AdminLabel({ label, help }: { label: string; help?: string }) {
  return <span className="admin-label-with-info"><span>{label}</span><AdminInfo label={label} help={help || adminHelp(label)} /></span>;
}

export function AdminFieldLabel({ htmlFor, label, help }: { htmlFor: string; label: string; help: string }) {
  return <span className="admin-label-with-info"><label htmlFor={htmlFor}>{label}</label><AdminInfo label={label} help={help} /></span>;
}

export function AdminHeading({ label, help, level = 3, id }: { label: string; help?: string; level?: 2 | 3 | 4; id?: string }) {
  const Heading = level === 2 ? "h2" : level === 4 ? "h4" : "h3";
  return <Heading id={id} aria-label={label}><AdminLabel label={label} help={help} /></Heading>;
}
