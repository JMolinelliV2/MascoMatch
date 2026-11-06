"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { InputHTMLAttributes, ReactNode } from "react";
import { applySuggestion, matchingSuggestions } from "@/lib/suggestions";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "list" | "value" | "defaultValue" | "onChange" | "multiple"> & {
  label: string; options: readonly string[]; optional?: boolean; help?: ReactNode; error?: string;
  value?: string; defaultValue?: string; onValueChange?: (value: string) => void; multiple?: boolean;
};

/** An editable combobox: suggestions never restrict custom values or alter form names. */
export function SuggestionField({ label, options, optional = false, help, error, value, defaultValue = "", onValueChange, multiple = false, id: suppliedId, ...inputProps }: Props) {
  const generatedId = useId();
  const id = suppliedId || generatedId;
  const root = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const composing = useRef(false);
  const [draft, setDraft] = useState(defaultValue);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [placement, setPlacement] = useState({ above: false, maxHeight: 260 });
  const current = value ?? draft;
  const suggestions = matchingSuggestions(options, current, multiple).filter(option => inputProps.maxLength === undefined || applySuggestion(current, option, multiple).length <= inputProps.maxLength);
  const expanded = open && !inputProps.disabled && !inputProps.readOnly;
  const activeIndex = active < suggestions.length ? active : -1;

  useEffect(() => {
    if (!expanded) return;
    function dismiss(event: Event) {
      if (event.target instanceof Node && !root.current?.contains(event.target)) setOpen(false);
    }
    function position() {
      const bounds = input.current?.getBoundingClientRect();
      if (!bounds) return;
      const below = window.innerHeight - bounds.bottom - 12;
      const above = bounds.top - 12;
      const upwards = below < 180 && above > below;
      setPlacement({ above: upwards, maxHeight: Math.max(44, Math.min(260, upwards ? above : below)) });
    }
    position();
    document.addEventListener("pointerdown", dismiss, true);
    document.addEventListener("focusin", dismiss);
    window.addEventListener("resize", position);
    window.addEventListener("scroll", position, true);
    return () => {
      document.removeEventListener("pointerdown", dismiss, true);
      document.removeEventListener("focusin", dismiss);
      window.removeEventListener("resize", position);
      window.removeEventListener("scroll", position, true);
    };
  }, [expanded]);

  useEffect(() => {
    if (expanded && activeIndex >= 0) list.current?.children[activeIndex]?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }, [expanded, activeIndex]);

  function choose(option: string) {
    const control = input.current;
    if (!control || control.matches(":disabled")) return;
    const next = applySuggestion(current, option, multiple);
    // Use the same native input event as typing, including the enclosing form's
    // onChange (validation and idempotent submissions depend on that event).
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
    setter?.call(control, next);
    control.dispatchEvent(new Event("input", { bubbles: true }));
    setOpen(false); setActive(-1);
  }

  return <div ref={root} className="field-label suggestion-field">
    <label htmlFor={id}>{label} {optional && <span className="optional">(opcional)</span>}</label>
    <div className="suggestion-control">
      <input {...inputProps} ref={input} id={id} className={`form-input ${inputProps.className || ""}`} value={current} autoComplete="off"
        role="combobox" aria-autocomplete="list" aria-expanded={expanded} aria-controls={expanded ? `${id}-suggestions` : undefined}
        aria-activedescendant={expanded && activeIndex >= 0 ? `${id}-option-${activeIndex}` : undefined}
        aria-invalid={Boolean(error) || inputProps["aria-invalid"]}
        aria-describedby={[inputProps["aria-describedby"], help ? `${id}-help` : "", error ? `${id}-error` : ""].filter(Boolean).join(" ") || undefined}
        onChange={event => { const next = event.target.value; setDraft(next); onValueChange?.(next); setActive(-1); setOpen(true); }}
        onFocus={event => { setOpen(true); setActive(-1); inputProps.onFocus?.(event); }}
        onClick={event => { setOpen(true); inputProps.onClick?.(event); }}
        onBlur={event => { setOpen(false); inputProps.onBlur?.(event); }}
        onCompositionStart={event => { composing.current = true; inputProps.onCompositionStart?.(event); }}
        onCompositionEnd={event => { composing.current = false; inputProps.onCompositionEnd?.(event); }}
        onKeyDown={event => {
          inputProps.onKeyDown?.(event);
          if (event.defaultPrevented || composing.current || event.nativeEvent.isComposing) return;
          if (event.key === "Escape" && expanded) { event.preventDefault(); event.stopPropagation(); setOpen(false); setActive(-1); }
          else if ((event.key === "ArrowDown" || event.key === "ArrowUp") && suggestions.length) {
            event.preventDefault(); setOpen(true);
            setActive(event.key === "ArrowDown" ? !expanded || activeIndex < 0 ? 0 : (activeIndex + 1) % suggestions.length
              : !expanded || activeIndex < 0 ? suggestions.length - 1 : (activeIndex - 1 + suggestions.length) % suggestions.length);
          } else if (event.key === "Enter" && expanded && activeIndex >= 0) { event.preventDefault(); choose(suggestions[activeIndex]); }
          else if (event.key === "Tab" || event.key === "Enter") setOpen(false);
        }} />
      {expanded && <div className={`suggestion-panel${placement.above ? " suggestion-panel--above" : ""}`} style={{ maxHeight: placement.maxHeight }}>
        <ul ref={list} id={`${id}-suggestions`} role="listbox" aria-label={`Sugerencias de ${label}`}>
          {suggestions.map((option, index) => <li key={option} id={`${id}-option-${index}`} role="option" aria-selected={index === activeIndex}
            className={`suggestion-option${index === activeIndex ? " suggestion-option--active" : ""}`}
            onPointerDown={event => event.preventDefault()} onClick={() => choose(option)} onPointerMove={event => { if (event.pointerType !== "touch") setActive(index); }}>{option}</li>)}
        </ul>
        {!suggestions.length && <p className="suggestion-empty" role="status">Podés usar el texto que escribiste, aunque no esté en las sugerencias.</p>}
      </div>}
    </div>
    {help && <span id={`${id}-help`} className="field-help">{help}</span>}
    {error && <span id={`${id}-error`} className="field-error" role="alert">{error}</span>}
  </div>;
}
