"use client";

import Image from "next/image";
import Link from "next/link";
import { useId, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { Icon } from "./ui/pictogram";
import "./home-how-it-works.css";

const steps = [
  {
    id: "notice", label: "Tu aviso", hint: "Empieza la búsqueda", icon: "paw", tone: "coral",
    title: "Todo empieza con un aviso.",
    description: "Contanos cómo es tu mascota y dónde la viste por última vez. Una descripción, una fecha aproximada y una foto clara ayudan a que otras personas puedan reconocerla.",
    detail: "Creá una cuenta y confirmá tu correo para publicar. Las fotos son opcionales y podés agregarlas después desde Mis avisos.",
    action: "Publicar una mascota perdida", href: "/perdi",
  },
  {
    id: "sighting", label: "Una pista", hint: "La comunidad se suma", icon: "pin", tone: "blue",
    title: "Alguien la ve. Una pista se suma.",
    description: "La comunidad puede explorar los animales perdidos y el mapa. Desde la ficha de una mascota, alcanza con indicar dónde y cuándo se la vio, y sumar fotos si hay.",
    detail: "El avistamiento breve desde un aviso se envía sin cuenta. Si el animal todavía no está publicado, se puede crear un reporte desde “Vi una mascota”.",
    action: "Ver animales perdidos", href: "/perdidos",
  },
  {
    id: "review", label: "La comparación", hint: "Cada detalle cuenta", icon: "spark", tone: "blue",
    title: "Las pistas llegan para revisar.",
    description: "Comparamos fotos, características, lugar y fecha con las búsquedas activas. Las alertas se consultan en la cuenta y también pueden llegar por correo, según las preferencias de notificación.",
    detail: "La IA propone posibles coincidencias. Cada una necesita revisión humana: mirá las fotos, la zona y la fecha. Un avistamiento enviado desde tu aviso también llega como pista, aunque su comparación esté pendiente o no resulte compatible.",
    action: "Explorar los reportes en el mapa", href: "/mapa",
  },
  {
    id: "reunion", label: "El reencuentro", hint: "De vuelta en casa", icon: "heart", tone: "green",
    title: "Cuando vuelve, la búsqueda se cierra.",
    description: "Confirmar que un avistamiento corresponde a tu mascota registra una pista. Cuando ya esté con vos, marcá “Ya la recuperé” desde Mis avisos para retirar el aviso de las búsquedas activas.",
    detail: "Son dos momentos distintos: una pista confirmada mantiene la búsqueda abierta. El reencuentro indica que la mascota ya volvió con su familia.",
    action: "Seguir ayudando a otras mascotas", href: "/perdidos",
  },
] as const;

const exampleLocations = [
  { label: "Cerca de la plaza", left: "26%", top: "45%" },
  { label: "En la esquina indicada", left: "54%", top: "65%" },
  { label: "Junto al parque", left: "77%", top: "29%" },
];

function ExamplePhoto({ visible = true }: { visible?: boolean }) {
  return <div className="how-example-photo">
    {visible ? <Image src="/images/dog-hero-generated.jpg" alt="Imagen ilustrativa de un golden retriever para este ejemplo" fill sizes="112px" /> : <Icon name="paw" />}
  </div>;
}

export function HomeHowItWorks() {
  const componentId = useId();
  const [active, setActive] = useState(0);
  const [withPhoto, setWithPhoto] = useState(true);
  const [location, setLocation] = useState(0);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [resolution, setResolution] = useState<"active" | "sighting" | "found">("active");
  const tabButtons = useRef<(HTMLButtonElement | null)[]>([]);

  function navigateTabs(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    let next: number;
    switch (event.key) {
      case "ArrowRight": next = (index + 1) % steps.length; break;
      case "ArrowLeft": next = (index + steps.length - 1) % steps.length; break;
      case "Home": next = 0; break;
      case "End": next = steps.length - 1; break;
      default: return;
    }
    event.preventDefault();
    setActive(next);
    tabButtons.current[next]?.focus();
  }

  function example(step: typeof steps[number]) {
    if (step.id === "notice") return <>
      <div className="how-notice-example">
        <div className="how-example-card-heading"><span>Un aviso para compartir</span><Icon name="paw" /></div>
        <div className="how-example-animal"><ExamplePhoto visible={withPhoto} /><div><h4>Tu mascota</h4><p>Sus rasgos, su última zona y una foto para reconocerla.</p><span className="how-example-status">Búsqueda activa</span></div></div>
      </div>
      <button type="button" className="how-demo-button" aria-pressed={withPhoto} onClick={() => setWithPhoto(value => !value)}><Icon name="camera" />Incluir foto en el ejemplo{withPhoto && <Icon name="check" />}</button>
      <p className="how-example-tip" role="status">{withPhoto ? "Una foto clara puede ayudar a reconocerla." : "La foto es opcional. Se puede agregar después."}</p>
    </>;

    if (step.id === "sighting") return <>
      <div className="how-example-map">
        <svg className="how-map-illustration" viewBox="0 0 420 260" aria-hidden="true" focusable="false">
          <rect width="420" height="260" fill="#e9f0eb" />
          <rect x="20" y="28" width="115" height="84" rx="20" fill="#cce5d6" />
          <rect x="266" y="120" width="136" height="115" rx="26" fill="#cce5d6" />
          <path d="M-20 205 290-20M80 290 430 38M-25 37 438 234" fill="none" stroke="#fff" strokeWidth="22" />
          <path d="M-20 205 290-20M80 290 430 38M-25 37 438 234" fill="none" stroke="#d8e0df" strokeWidth="2" />
          <path d="M0 140h420M187 0v260" fill="none" stroke="#fff" strokeWidth="13" />
          <path d="M110 118Q190 76 225 165T320 75" fill="none" stroke="#0863b4" strokeWidth="3" strokeDasharray="5 7" strokeLinecap="round" />
        </svg>
        <span className="how-map-label"><Icon name="pin" />Zona del avistamiento</span>
        {exampleLocations.map((point, index) => <button key={point.label} type="button" className="how-example-pin" style={{ left: point.left, top: point.top }} aria-label={`Elegir ubicación de ejemplo: ${point.label}`} aria-pressed={location === index} onClick={() => setLocation(index)}><Icon name="pin" /></button>)}
      </div>
      <p className="how-example-location" role="status"><Icon name="pin" />{exampleLocations[location].label}</p>
      <p className="how-example-tip">Tocá un punto del mapa para probar otra ubicación.</p>
    </>;

    if (step.id === "review") return <>
      <div className="how-alert-example">
        <div className="how-example-card-heading"><span className="how-alert-icon"><Icon name="bell" /></span><span>Una nueva pista</span></div>
        <div className="how-example-animal"><ExamplePhoto /><div><h4>Un avistamiento para revisar</h4><p>Las fotos y los detalles pueden ayudar a reconocer al animal.</p></div></div>
        <button type="button" className="how-demo-button" aria-expanded={reviewOpen} aria-controls={`${componentId}-review-details`} onClick={() => setReviewOpen(value => !value)}>{reviewOpen ? "Ocultar los detalles" : "Ver qué conviene revisar"}<Icon name="chevron" /></button>
        <ul id={`${componentId}-review-details`} className="how-review-details" hidden={!reviewOpen}>
          <li><Icon name="camera" />Fotos y rasgos distintivos</li>
          <li><Icon name="pin" />La zona del avistamiento</li>
          <li><Icon name="calendar" />La fecha y la hora aproximada</li>
        </ul>
      </div>
      <p className="how-example-tip">Una posible coincidencia es una pista, no una identidad confirmada.</p>
    </>;

    return <>
      <div className="how-reunion-example" data-found={resolution === "found"}>
        <div className="how-reunion-photo"><ExamplePhoto /><span className="how-reunion-heart" aria-hidden="true"><Icon name={resolution === "found" ? "heart" : "paw"} /></span></div>
        <h4>{resolution === "found" ? "De vuelta en casa" : "La búsqueda sigue activa"}</h4>
        <p role="status">{resolution === "found" ? "En este ejemplo, el aviso deja de aparecer entre los animales perdidos." : resolution === "sighting" ? "En este ejemplo, la pista está confirmada y la búsqueda sigue abierta." : "Probá las dos acciones para ver la diferencia."}</p>
        <div className="how-resolution-options" role="group" aria-label="Acciones de ejemplo para el estado del aviso">
          <button type="button" aria-pressed={resolution === "sighting"} onClick={() => setResolution("sighting")}><Icon name="eye" />Confirmar una pista</button>
          <button type="button" aria-pressed={resolution === "found"} onClick={() => setResolution("found")}><Icon name="heart" />Ya la recuperé</button>
        </div>
      </div>
    </>;
  }

  return <section id="como-funciona" className="how-it-works" aria-labelledby="how-title">
    <div className="how-heading">
      <p className="eyebrow">Cada pista puede ayudar</p>
      <h2 id="how-title">Cómo funciona <span className="title-accent">MascoMatch</span></h2>
      <p className="how-intro">Un aviso empieza la búsqueda. La comunidad suma pistas y cada familia las revisa para acercarse al reencuentro.</p>
      <p className="how-explore-hint"><Icon name="paw" />Elegí un paso y probá los ejemplos.</p>
    </div>
    <div className="how-step-tabs" role="tablist" aria-label="Recorrido de MascoMatch">
      {steps.map((step, index) => <button key={step.id} ref={element => { tabButtons.current[index] = element; }} id={`${componentId}-tab-${step.id}`} className="how-step-tab" type="button" role="tab" aria-selected={active === index} aria-controls={`${componentId}-panel-${step.id}`} tabIndex={active === index ? 0 : -1} data-tone={step.tone} onClick={() => setActive(index)} onKeyDown={event => navigateTabs(event, index)}>
        <span className="how-tab-icon"><Icon name={step.icon} /></span><span className="how-tab-text"><strong>{step.label}</strong><span>{step.hint}</span></span><span className="how-tab-number" aria-hidden="true">0{index + 1}</span>
      </button>)}
    </div>
    <div className="how-story">
      {steps.map((step, index) => <div key={step.id} id={`${componentId}-panel-${step.id}`} className="how-panel" role="tabpanel" aria-labelledby={`${componentId}-tab-${step.id}`} hidden={active !== index} tabIndex={active === index ? 0 : -1} data-tone={step.tone}>
        <div className="how-panel-copy"><p className="how-panel-step">Paso 0{index + 1}<span aria-hidden="true"> · </span>{step.hint}</p><h3>{step.title}</h3><p className="how-panel-description">{step.description}</p><div className="how-panel-detail"><Icon name="shield" /><p>{step.detail}</p></div><Link href={step.href} className="button button-primary how-panel-action">{step.action}<Icon name="arrow" /></Link></div>
        <div className="how-scene"><p className="how-scene-label"><Icon name="spark" />Ejemplo ilustrativo</p>{example(step)}</div>
      </div>)}
      <div className="how-controls"><button type="button" className="text-button how-previous" disabled={active === 0} onClick={() => setActive(value => Math.max(0, value - 1))}><Icon name="arrow" />Anterior</button><p role="status" aria-live="polite" aria-atomic="true"><span className="sr-only">Paso </span><strong>0{active + 1}</strong> / 04<span className="sr-only">: {steps[active].label}</span></p><button type="button" className="text-button" onClick={() => setActive(value => (value + 1) % steps.length)}>{active === steps.length - 1 ? "Volver al principio" : "Siguiente paso"}<Icon name="arrow" /></button></div>
    </div>
  </section>;
}
