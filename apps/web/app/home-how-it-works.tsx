"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Icon } from "./ui/pictogram";
import "./home-how-it-works.css";

const steps = [
  {
    id: "notice", hint: "El primer paso", tone: "coral", icon: "camera",
    image: { src: "/images/how-notice-manypixels.svg", width: 500, height: 500, kind: "library" },
    title: "Publicá su aviso.",
    description: "Contanos cómo es tu mascota, dónde la viste por última vez y cuándo. Una foto clara ayuda a reconocerla y hace que su aviso sea más fácil de compartir.",
    detailTitle: "Antes de publicar",
    detail: "Creá una cuenta y confirmá tu correo. Las fotos son opcionales: si todavía no tenés una, podés publicar y agregarla después desde Mis avisos.",
    action: "Publicar una mascota perdida", href: "/perdi",
  },
  {
    id: "sighting", hint: "La comunidad se suma", tone: "blue", icon: "pin",
    image: { src: "/images/how-sighting-reference.webp", width: 1536, height: 1024, kind: "adapted" },
    title: "Una mirada puede ser la pista.",
    description: "Alguien reconoce a una mascota en la calle. Desde su aviso puede indicar dónde y cuándo la vio, y sumar una foto si tiene. Ese avistamiento breve se puede enviar sin cuenta.",
    detailTitle: "Si todavía no hay un aviso",
    detail: "Con una cuenta, podés crear un reporte desde “Vi una mascota”. Si el animal está a salvo con vos, elegí “Encontré una mascota” para que su familia pueda encontrarlo.",
    action: "Ver animales perdidos", href: "/perdidos",
  },
  {
    id: "review", hint: "Cada detalle cuenta", tone: "blue", icon: "spark",
    image: { src: "/images/how-review-reference.webp", width: 1685, height: 933, kind: "adapted" },
    title: "La tecnología conecta. Vos revisás.",
    description: "MascoMatch compara fotos, características, zona y fecha para acercarte posibles coincidencias. Las pistas llegan a tu cuenta y también pueden llegar por correo, según tus preferencias.",
    detailTitle: "Cómo llegan las pistas",
    detail: "La IA sugiere coincidencias y cada familia revisa los detalles. Un avistamiento enviado desde tu aviso también llega como pista, aunque la comparación esté pendiente o no resulte compatible.",
    action: "Explorar el mapa", href: "/mapa",
  },
  {
    id: "reunion", hint: "De vuelta en casa", tone: "green", icon: "heart",
    image: { src: "/images/how-reunion-reference.webp", width: 1222, height: 1287, kind: "adapted" },
    title: "El reencuentro cierra la búsqueda.",
    description: "Cuando tu mascota ya esté con vos, marcá “Ya la recuperé” desde Mis avisos. Su aviso deja de aparecer entre los animales perdidos y podés compartir una reseña sobre tu experiencia.",
    detailTitle: "¿Y si confirmé un avistamiento?",
    detail: "Confirmar que es tu mascota registra una pista y mantiene la búsqueda abierta. Marcá la recuperación cuando efectivamente haya vuelto con vos.",
    action: "Seguir ayudando", href: "/perdidos",
  },
] as const;

type Route = { path: string; width: number; height: number };

export function HomeHowItWorks() {
  const journey = useRef<HTMLOListElement>(null);
  const progressPath = useRef<SVGPathElement>(null);
  const [route, setRoute] = useState<Route | null>(null);

  useEffect(() => {
    const list = journey.current;
    if (!list) return;

    const rows = Array.from(list.querySelectorAll<HTMLElement>(".how-journey-step"));
    const markers = Array.from(list.querySelectorAll<HTMLElement>("[data-how-marker]"));
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let frame = 0;
    let needsLayout = true;
    let disposed = false;

    function update() {
      frame = 0;
      if (!list || disposed) return;
      const bounds = list.getBoundingClientRect();
      const points = markers.map(marker => {
        const rect = marker.getBoundingClientRect();
        return { x: rect.left + rect.width / 2 - bounds.left, y: rect.top + rect.height / 2 - bounds.top };
      });
      if (points.length !== steps.length || !bounds.width || !bounds.height) return;

      if (needsLayout) {
        const bend = window.matchMedia("(max-width: 760px)").matches ? 12 : 58;
        let path = `M ${points[0].x} ${points[0].y}`;
        points.slice(1).forEach((point, index) => {
          const previous = points[index];
          const offset = (index % 2 === 0 ? 1 : -1) * bend;
          const distance = point.y - previous.y;
          path += ` C ${previous.x + offset} ${previous.y + distance * .3}, ${point.x + offset} ${point.y - distance * .3}, ${point.x} ${point.y}`;
        });
        setRoute({ path, width: bounds.width, height: bounds.height });
        needsLayout = false;
      }

      const readingLine = window.innerHeight * .6 - bounds.top;
      const first = points[0].y;
      const last = points[points.length - 1].y;
      const progress = Math.min(1, Math.max(0, (readingLine - first) / Math.max(1, last - first)));
      if (progressPath.current) progressPath.current.style.strokeDashoffset = String(1000 * (1 - progress));
      const active = points.reduce((current, point, index) => point.y <= readingLine ? index : current, -1);
      rows.forEach((row, index) => {
        row.dataset.visited = String(index <= active);
        row.dataset.current = String(index === active);
      });
    }

    function schedule(layout = false) {
      needsLayout ||= layout;
      if (!frame) frame = window.requestAnimationFrame(update);
    }

    const onScroll = () => schedule();
    const onResize = () => schedule(true);
    const resizeObserver = typeof ResizeObserver !== "undefined" ? new ResizeObserver(onResize) : null;
    resizeObserver?.observe(list);
    rows.forEach(row => resizeObserver?.observe(row));
    const enterObserver = typeof IntersectionObserver !== "undefined" ? new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        if (!motion.matches) (entry.target as HTMLElement).dataset.entered = "true";
        enterObserver?.unobserve(entry.target);
      });
    }, { threshold: .12 }) : null;
    rows.forEach(row => enterObserver?.observe(row));

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize);
    list.addEventListener("toggle", onResize, true);
    // Recalculate after fonts settle, including browsers without ResizeObserver.
    document.fonts?.ready.then(() => { if (!disposed) schedule(true); });
    schedule(true);

    return () => {
      disposed = true;
      window.cancelAnimationFrame(frame);
      resizeObserver?.disconnect();
      enterObserver?.disconnect();
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
      list.removeEventListener("toggle", onResize, true);
    };
  }, []);

  // The initial SVG mount happens after the first layout calculation.
  useEffect(() => {
    const list = journey.current;
    if (!route || !list || !progressPath.current) return;
    const markers = list.querySelectorAll<HTMLElement>("[data-how-marker]");
    const first = markers[0].getBoundingClientRect();
    const last = markers[markers.length - 1].getBoundingClientRect();
    const start = first.top + first.height / 2;
    const end = last.top + last.height / 2;
    const progress = Math.min(1, Math.max(0, (window.innerHeight * .6 - start) / Math.max(1, end - start)));
    progressPath.current.style.strokeDashoffset = String(1000 * (1 - progress));
  }, [route]);

  return <section id="como-funciona" className="how-it-works" aria-labelledby="how-title">
    <header className="how-heading">
      <p className="eyebrow">Una red para volver a casa</p>
      <h2 id="how-title">Cómo funciona <span className="title-accent">MascoMatch</span></h2>
      <p className="how-intro">Desde el primer aviso hasta el reencuentro,<br className="how-desktop-break" /> cada persona puede sumar una pista.</p>
      <a href="#how-notice" className="how-start-link">Seguí el recorrido <Icon name="arrow" /></a>
    </header>

    <ol ref={journey} className="how-journey" data-route-ready={route !== null} aria-label="Los cuatro pasos de MascoMatch">
      {steps.map((step, index) => <li key={step.id} id={`how-${step.id}`} className="how-journey-step" data-tone={step.tone}>
        {index === 0 && route && <svg className="how-route how-route-layer" viewBox={`0 0 ${route.width} ${route.height}`} preserveAspectRatio="none" aria-hidden="true" focusable="false">
          <path className="how-route-base" d={route.path} />
          <path ref={progressPath} className="how-route-progress" d={route.path} pathLength="1000" />
        </svg>}
        <span className="how-checkpoint" data-how-marker aria-hidden="true">0{index + 1}</span>
        <div className="how-illustration" data-image-kind={step.image.kind} aria-hidden="true">
          <Image src={step.image.src} alt="" width={step.image.width} height={step.image.height} sizes="(max-width: 760px) 300px, (max-width: 1000px) 280px, 360px" />
          <span className="how-illustration-stamp"><Icon name={step.icon} /></span>
        </div>
        <div className="how-step-copy">
          <p className="how-step-eyebrow"><span className="sr-only">Paso {index + 1}: </span>{step.hint}</p>
          <h3>{step.title}</h3>
          <p className="how-step-description">{step.description}</p>
          <details className="how-step-detail">
            <summary>{step.detailTitle}<Icon name="chevron" /></summary>
            <p>{step.detail}</p>
          </details>
          <Link href={step.href} className={`how-step-action${index === 0 ? " button button-primary" : ""}`}>{step.action}<Icon name="arrow" /></Link>
        </div>
      </li>)}
    </ol>
    <p className="how-closing"><Icon name="heart" />Una foto, una mirada, una pista. Cada ayuda cuenta.</p>
  </section>;
}
