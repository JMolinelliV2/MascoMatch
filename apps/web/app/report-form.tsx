"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import type { Place } from "@/lib/places";
import { LocationPicker } from "./location-picker";
import { ReportAnalysis } from "./report-analysis";

type ReportKind = "lost" | "sighting" | "found";
type AccountMode = "register" | "login";
type Step = 1 | 2 | 3;
type Review = { animal: string; description: string; when: string; note: string };
type FormControl = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const inputClass = "form-input";
const labels: Record<ReportKind, { title: string; intro: string; submit: string; event: string }> = {
  lost: { title: "Perdí una mascota", intro: "Completá sus datos y el último lugar donde la viste.", submit: "Publicar mascota perdida", event: "Dónde y cuándo se perdió" },
  sighting: { title: "Vi una mascota", intro: "Describí al animal e indicá dónde lo viste.", submit: "Publicar avistamiento", event: "Dónde y cuándo lo viste" },
  found: { title: "Encontré una mascota", intro: "Registrá sus datos y dónde lo encontraste.", submit: "Publicar animal encontrado", event: "Dónde y cuándo lo encontraste" },
};

class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

async function readResponse<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "";
    if (response.status === 401) throw new ApiError("El correo o la contraseña no son correctos.", 401);
    if (response.status === 409 && detail.includes("email")) {
      throw new ApiError("Ya existe una cuenta con ese correo. Elegí “Ya tengo cuenta” para ingresar.", 409);
    }
    throw new ApiError(detail || "No pudimos guardar el reporte. Revisá los datos e intentá de nuevo.", response.status);
  }
  return data as T;
}

async function send<T>(path: string, body: object, token?: string): Promise<T> {
  const response = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify(body),
  });
  return readResponse<T>(response);
}

async function sendPhoto(file: File, ownerType: string, ownerId: string, token: string) {
  const form = new FormData();
  form.append("owner_type", ownerType);
  form.append("owner_id", ownerId);
  form.append("file", file);
  const response = await fetch(`${API}/photos/upload`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: form });
  await readResponse(response);
}

function Section({ title, number, active, children }: { title: string; number: Step; active: Step; children: ReactNode }) {
  return (
    <fieldset className="form-section" data-step={number} hidden={active !== number}>
      <legend className="sr-only">{title}</legend>
      <div className="section-fields">{children}</div>
    </fieldset>
  );
}

export function ReportForm({ kind }: { kind: ReportKind }) {
  const formRef = useRef<HTMLFormElement>(null);
  const stepHeadingRef = useRef<HTMLHeadingElement>(null);
  const pendingFocus = useRef<{ name: string; native: boolean } | null>(null);
  const [step, setStep] = useState<Step>(1);
  const [review, setReview] = useState<Review | null>(null);
  const [savedReport, setSavedReport] = useState<{ ownerType: "lost_case" | "observation"; ownerId: string; token: string } | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [photoWarning, setPhotoWarning] = useState("");
  const [busy, setBusy] = useState(false);
  const [accountMode, setAccountMode] = useState<AccountMode>("register");
  const [location, setLocation] = useState<Place | null>(null);
  const [locationError, setLocationError] = useState("");
  const [resetCount, setResetCount] = useState(0);
  const [photo, setPhoto] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const copy = labels[kind];
  const stepTitles = [kind === "lost" ? "Contanos sobre tu mascota" : "Contanos sobre el animal", copy.event, "Revisá el reporte y dejá tu contacto"];
  const stepIntros = ["Empezá por sus características. Los campos opcionales pueden quedar vacíos.", "La fecha y la hora pueden ser aproximadas. Elegí el lugar por su nombre o dirección.", "Podés editar los datos antes de publicar. Tu contacto se guarda con tu cuenta."];

  useEffect(() => {
    const target = pendingFocus.current;
    if (!target) return;
    pendingFocus.current = null;
    if (target.name === "heading") { stepHeadingRef.current?.focus(); return; }
    const control = formRef.current?.elements.namedItem(target.name) as FormControl | null;
    control?.focus();
    if (target.native) control?.reportValidity();
  }, [step]);

  useEffect(() => {
    if (!photo) { setPreview(""); return; }
    const url = URL.createObjectURL(photo);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [photo]);

  function goToStep(next: Step) {
    setError("");
    pendingFocus.current = { name: "heading", native: false };
    setStep(next);
  }

  function invalid(formElement: HTMLFormElement, target: Step, name: string, message: string, native = false) {
    setError(message);
    if (target !== step) {
      pendingFocus.current = { name, native };
      setStep(target);
    } else {
      const control = formElement.elements.namedItem(name) as FormControl | null;
      control?.focus();
      if (native) control?.reportValidity();
    }
    return false;
  }

  function validateStage(formElement: HTMLFormElement, target: Step) {
    const form = new FormData(formElement);
    const text = (key: string) => String(form.get(key) ?? "").trim();
    const controls = formElement.querySelectorAll<FormControl>(`[data-step="${target}"] input, [data-step="${target}"] select, [data-step="${target}"] textarea`);
    // Only validate the current topic; hidden stages stay mounted to preserve their values.
    for (const control of controls) {
      control.setCustomValidity("");
      if (control.required && ["petName", "description", "name"].includes(control.name) && !text(control.name)) {
        control.setCustomValidity("Completá este campo.");
      }
    }
    for (const control of controls) {
      if (control.name !== "locationSearch" && !control.checkValidity()) {
        return invalid(formElement, target, control.name, control.validationMessage, true);
      }
    }
    if (target === 2 && ((kind === "lost" && !location) || (!location && text("locationSearch")))) {
      const message = kind === "lost"
        ? "Elegí un lugar de la lista o usá la ubicación del dispositivo."
        : "Para guardar ese lugar, elegí uno de los resultados de búsqueda.";
      setLocationError(message);
      return invalid(formElement, 2, "locationSearch", message);
    }
    if (target === 1 && photo) {
      if (photo.size > 10 * 1024 * 1024) return invalid(formElement, 1, "photo", "La foto no puede superar los 10 MB.");
      if (!["image/jpeg", "image/png", "image/webp"].includes(photo.type)) {
        return invalid(formElement, 1, "photo", "La foto debe ser JPEG, PNG o WebP.");
      }
    }
    if (target === 2) {
      const when = new Date(text("observedAt"));
      if (!Number.isFinite(when.getTime()) || when.getTime() > Date.now() + 60_000) {
        return invalid(formElement, 2, "observedAt", "Ingresá una fecha y hora válidas, que no estén en el futuro.");
      }
    }
    return true;
  }

  function updateReview(formElement: HTMLFormElement) {
    const form = new FormData(formElement);
    const text = (key: string) => String(form.get(key) ?? "").trim();
    const selected = (key: string) => formElement.querySelector<HTMLSelectElement>(`[name="${key}"]`)?.selectedOptions[0]?.textContent ?? "";
    setReview({
      animal: [kind === "lost" ? text("petName") : "", selected("species"), text("sex") !== "unknown" ? selected("sex") : "", text("color") !== "unknown" ? selected("color") : "", text("size") !== "unknown" ? selected("size") : ""].filter(Boolean).join(" · "),
      description: text("description"),
      when: text("observedAt"),
      note: kind === "lost" ? "" : text("eventNote"),
    });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const formElement = event.currentTarget;
    setError("");
    setSuccess("");
    setPhotoWarning("");
    setLocationError("");
    const form = new FormData(formElement);
    const text = (key: string) => String(form.get(key) ?? "").trim();
    if (step < 3) {
      if (!validateStage(formElement, step)) return;
      if (step === 2) updateReview(formElement);
      goToStep((step + 1) as Step);
      return;
    }
    for (const target of [1, 2, 3] as const) {
      if (!validateStage(formElement, target)) return;
    }
    const when = new Date(text("observedAt"));
    setBusy(true);
    try {
      const session = await send<{ access_token: string }>(`/auth/${accountMode}`, {
        email: text("email").toLowerCase(),
        password: String(form.get("password") ?? ""),
        ...(accountMode === "register" ? { name: text("name") } : {}),
      });
      const token = session.access_token;
      const species = text("species");
      const sex = text("sex");
      const color = text("color");
      const size = text("size");
      // Exact addresses stay in the picker; reports include only the locality.
      const placeDescription = location?.locality ? `Zona: ${location.locality}` : "";
      // Preserve both the animal description and the context in the original report.
      const description = [
        text("description"),
        color !== "unknown" ? `Color principal: ${formElement.querySelector<HTMLSelectElement>('[name="color"]')?.selectedOptions[0].textContent}.` : "",
        size !== "unknown" ? `Tamaño: ${formElement.querySelector<HTMLSelectElement>('[name="size"]')?.selectedOptions[0].textContent}.` : "",
        placeDescription,
        kind !== "lost" && text("eventNote") ? `Detalles del reporte: ${text("eventNote")}` : "",
      ].filter(Boolean).join("\n\n");
      const locationData = location ? {
        latitude: location.latitude,
        longitude: location.longitude,
        ...(location.accuracyMeters === undefined ? {} : { location_accuracy_meters: location.accuracyMeters }),
      } : {};
      let report: { id: string };
      let ownerType: "lost_case" | "observation";
      if (kind === "lost") {
        const pet = await send<{ id: string }>("/pets", {
          name: text("petName"), species, sex, primary_color: color, size, breed: "unknown",
        }, token);
        report = await send("/lost-cases", {
          pet_id: pet.id, lost_at: when.toISOString(), last_seen_at: when.toISOString(),
          ...locationData, description,
          public_location: location?.locality ?? null,
        }, token);
        ownerType = "lost_case";
      } else {
        report = await send("/observations", {
          species, sex, description, observed_at: when.toISOString(), ...locationData,
          source_type: kind === "found" ? "FOUND_ANIMAL" : "USER_SIGHTING",
        }, token);
        ownerType = "observation";
      }
      if (photo) {
        try { await sendPhoto(photo, ownerType, report.id, token); }
        catch { setPhotoWarning("El reporte se guardó, pero la foto no pudo subirse. La información que compartiste quedó registrada."); }
      }
      setSuccess(kind === "lost" ? `El aviso de ${text("petName")} quedó guardado.` : "Gracias por ayudar. Tu reporte quedó guardado.");
      setSavedReport({ ownerType, ownerId: report.id, token });
      formElement.reset();
      setLocation(null);
      setPhoto(null);
      setResetCount(count => count + 1);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "No pudimos conectarnos. Verificá tu conexión e intentá de nuevo.");
    } finally {
      setBusy(false);
    }
  }

  if (success) {
    return (
      <main id="main-content" className="page report-page success-page">
        <span className="success-mark" aria-hidden="true">✓</span>
        <h1>Tu reporte quedó guardado</h1>
        <p role="status" className="page-intro">{success}</p>
        {photoWarning && <p role="alert" className="notice notice-warning">{photoWarning}</p>}
        {savedReport && <ReportAnalysis {...savedReport} />}
        <div className="success-actions">
          {kind === "lost" && <Link href="/perdidos" className="button button-primary">Ver animales perdidos</Link>}
          <Link href="/" className="button button-primary">Volver al inicio</Link>
          <button type="button" className="button button-secondary" onClick={() => {
            setSuccess(""); setPhotoWarning(""); setReview(null); setSavedReport(null); goToStep(1);
          }}>Crear otro reporte</button>
        </div>
      </main>
    );
  }

  return (
    <main id="main-content" className="page report-page">
      <Link href="/" className="back-link"><span aria-hidden="true">←</span> Volver al inicio</Link>
      <h1>{copy.title}</h1>
      <p className="page-intro">{copy.intro}</p>

      <form ref={formRef} onSubmit={submit} noValidate aria-busy={busy} className="report-form">
        <ol className="step-list" aria-label="Etapas del reporte">
          {["Mascota", "Fecha y lugar", "Contacto y revisión"].map((title, index) => (
            <li key={title} aria-current={step === index + 1 ? "step" : undefined}
              className={`step-item ${step === index + 1 ? "step-current" : step > index + 1 ? "step-complete" : ""}`}>
              <span className="step-number" aria-hidden="true">{step > index + 1 ? "✓" : index + 1}</span>
              <span>{title}<span className="sr-only">{step > index + 1 ? ", completado" : ""}</span></span>
            </li>
          ))}
        </ol>
        <div className="step-track" aria-hidden="true"><span style={{ width: `${step / 3 * 100}%` }} /></div>
        <p className="step-count">Paso {step} de 3</p>
        <h2 ref={stepHeadingRef} tabIndex={-1} className="step-heading">{stepTitles[step - 1]}</h2>
        <p className="step-intro">{stepIntros[step - 1]}</p>
        <fieldset disabled={busy} className="form-controls">
          <Section title={kind === "lost" ? "Mascota" : "Datos del animal"} number={1} active={step}>
            <div className="form-grid">
              <label className="field-label">Animal
                <select name="species" required defaultValue="" className={inputClass}>
                  <option value="" disabled>Seleccioná una opción</option>
                  <option value="dog">Perro</option><option value="cat">Gato</option>
                  <option value="rabbit">Conejo</option><option value="bird">Ave</option><option value="other">Otro</option>
                  {kind !== "lost" && <option value="unknown">No lo sé</option>}
                </select>
              </label>
              {kind === "lost" && <label className="field-label">Nombre
                <input name="petName" required minLength={1} maxLength={120} autoComplete="off" placeholder="Nombre de tu mascota" className={inputClass} />
              </label>}
              <label className="field-label">Sexo <span className="optional">(opcional)</span>
                <select name="sex" defaultValue="unknown" className={inputClass}>
                  <option value="unknown">No lo sé</option>
                  <option value="male">Macho</option><option value="female">Hembra</option>
                </select>
              </label>
              <label className="field-label">Color <span className="optional">(opcional)</span>
                <select name="color" defaultValue="unknown" className={inputClass}>
                  <option value="unknown">No lo sé</option><option value="brown">Marrón</option>
                  <option value="black">Negro</option><option value="white">Blanco</option><option value="gray">Gris</option>
                  <option value="cream">Crema</option><option value="orange">Naranja</option><option value="tan">Beige / canela</option>
                  <option value="red">Rojizo</option><option value="multicolor">Varios colores</option>
                </select>
              </label>
              <label className="field-label">Tamaño <span className="optional">(opcional)</span>
                <select name="size" defaultValue="unknown" className={inputClass}>
                  <option value="unknown">No lo sé</option><option value="tiny">Muy pequeño</option>
                  <option value="small">Pequeño</option><option value="medium">Mediano</option><option value="large">Grande</option>
                </select>
              </label>
            </div>
            <label className="field-label">Descripción
              <textarea name="description" required minLength={1} maxLength={2500} rows={3} aria-describedby="description-help" className={inputClass} />
              <span id="description-help" className="field-help">Contanos sobre sus colores, manchas, collar u otras características.</span>
            </label>
            <label className="field-label">Foto <span className="optional">(opcional)</span>
              <input name="photo" type="file" accept="image/jpeg,image/png,image/webp" onChange={event => setPhoto(event.target.files?.[0] ?? null)} className="file-input" />
              <span className="field-help">JPEG, PNG o WebP. Máximo 10 MB.</span>
            </label>
            {preview && photo?.type.startsWith("image/") && <div className="photo-info">
              <img src={preview} alt="Foto seleccionada" className="photo-preview" />
              <div><span>{photo.name}</span><br /><button type="button" className="text-button" onClick={() => {
                setPhoto(null);
                const input = formRef.current?.elements.namedItem("photo") as HTMLInputElement | null;
                if (input) input.value = "";
              }}>Quitar foto</button></div>
            </div>}
          </Section>

          <Section title={copy.event} number={2} active={step}>
            <label className="field-label">{kind === "lost" ? "Última vez que la viste" : "Fecha y hora"}
              <input name="observedAt" type="datetime-local" required className={inputClass} />
              <span className="field-help">La hora puede ser aproximada.</span>
            </label>
            <div>
              <LocationPicker key={resetCount} lost={kind === "lost"} required={kind === "lost"} value={location} onChange={place => { setLocation(place); setLocationError(""); }} />
              {locationError && <p role="alert" className="notice notice-error">{locationError}</p>}
            </div>
            {kind !== "lost" && <label className="field-label">Otra información <span className="optional">(opcional)</span>
              <textarea name="eventNote" maxLength={500} rows={2} placeholder="Por ejemplo, hacia dónde iba o quién lo está cuidando." className={inputClass} />
            </label>}
          </Section>

          <Section title="Contacto y revisión" number={3} active={step}>
            <section className="review-block" aria-labelledby="review-animal-title">
              <div className="review-heading">
                <h3 id="review-animal-title">Mascota</h3>
                <button type="button" className="text-button" onClick={() => goToStep(1)} aria-label="Editar los datos de la mascota">Editar</button>
              </div>
              <dl className="review-details">
                <div><dt>Datos del animal</dt><dd>{review?.animal}</dd></div>
                <div><dt>Descripción</dt><dd>{review?.description}</dd></div>
                <div><dt>Foto</dt><dd>{photo ? photo.name : "Sin foto"}</dd></div>
              </dl>
              {preview && photo?.type.startsWith("image/") && <img src={preview} alt="Foto que se adjuntará al reporte" className="photo-preview" />}
            </section>
            <section className="review-block" aria-labelledby="review-place-title">
              <div className="review-heading">
                <h3 id="review-place-title">Fecha y lugar</h3>
                <button type="button" className="text-button" onClick={() => goToStep(2)} aria-label="Editar la fecha y el lugar">Editar</button>
              </div>
              <dl className="review-details">
                <div><dt>Fecha y hora</dt><dd>{review?.when && new Intl.DateTimeFormat("es-UY", { dateStyle: "medium", timeStyle: "short" }).format(new Date(review.when))}</dd></div>
                <div><dt>Lugar</dt><dd>{location?.label ?? "No indicado"}</dd></div>
                {review?.note && <div><dt>Otra información</dt><dd>{review.note}</dd></div>}
              </dl>
            </section>
            <h3 className="contact-heading">Tu contacto</h3>
            <div className="account-options" role="group" aria-label="Opciones de cuenta">
              <label><input type="radio" name="accountMode" checked={accountMode === "register"} onChange={() => setAccountMode("register")} />Crear cuenta</label>
              <label><input type="radio" name="accountMode" checked={accountMode === "login"} onChange={() => setAccountMode("login")} />Ya tengo cuenta</label>
            </div>
            <div className="form-grid">
              {accountMode === "register" && <label className="field-label span-full">Tu nombre
                <input name="name" required minLength={1} maxLength={120} autoComplete="name" className={inputClass} />
              </label>}
              <label className="field-label">Correo electrónico
                <input name="email" type="email" required maxLength={320} autoComplete="email" className={inputClass} />
              </label>
              <label className="field-label">Contraseña
                <input name="password" type="password" required minLength={accountMode === "register" ? 10 : 1} maxLength={128} autoComplete={accountMode === "register" ? "new-password" : "current-password"} className={inputClass} />
                {accountMode === "register" && <span className="field-help">Mínimo 10 caracteres.</span>}
              </label>
            </div>
          </Section>

          <div className="form-footer">
            {error && <p role="alert" className="notice notice-error">{error}</p>}
            <div className="form-navigation">
              {step > 1 && <button type="button" className="button button-secondary" onClick={() => goToStep((step - 1) as Step)}>Atrás</button>}
              <button type="submit" disabled={busy} className="button button-primary submit-button">{busy ? "Guardando…" : step < 3 ? "Continuar →" : copy.submit}</button>
            </div>
            <p className="form-privacy">{step === 3 ? "Tu correo y la ubicación exacta no se muestran públicamente." : "Todavía no se publica nada. Podés revisar los datos al final."}</p>
          </div>
        </fieldset>
      </form>
    </main>
  );
}

