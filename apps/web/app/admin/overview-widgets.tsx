"use client";
import { Icon } from "../ui/pictogram";
import type { IconName } from "../ui/pictogram";
import { chartNumber, DonutChart, HorizontalBars, TimelineChart } from "./dashboard-charts";
import type { ChartSlice, TimelinePoint } from "./dashboard-charts";
import { AdminHeading, AdminLabel } from "./admin-info";
import { adminHelp } from "./admin-help";
export type Metric = { label: string; value: number; help: string };
export type OverviewCharts = { timeline: TimelinePoint[]; timeline_unit: string; jobs: ChartSlice[]; publications: ChartSlice[];
  accounts: { total: number; enabled: number; blocked: number; verified: number }; mail_kinds: ChartSlice[]; mail_status: Record<string, number> };
const featured: { label: string; icon: IconName; tone: string; eyebrow: string }[] = [
  { label: "Cuentas registradas", icon: "user", tone: "coral", eyebrow: "Comunidad" },
  { label: "Actividad en los últimos 15 min", icon: "clock", tone: "teal", eyebrow: "Actividad reciente" },
  { label: "Trabajos completados", icon: "layers", tone: "blue", eyebrow: "Procesamiento" },
  { label: "Correos enviados", icon: "mail", tone: "violet", eyebrow: "Comunicación" },
];
const mailLabels: Record<string, string> = { ALERT: "Alertas de avistamientos", VERIFY_EMAIL: "Confirmaciones de correo", RESET_PASSWORD: "Recuperaciones de contraseña", CHANGE_EMAIL: "Cambios de correo", PHOTO_REMINDER: "Recordatorios de fotos", CONTACT_FORWARD: "Mensajes de contacto" };
export function OverviewWidgets({ metrics, charts, queue, onQueue }: { metrics: Metric[]; charts?: OverviewCharts; queue?: { pending: number; failed: number }; onQueue: () => void }) {
  const remaining = metrics.filter(item => !featured.some(config => config.label === item.label));
  const recovered = metrics.find(item => item.label === "Mascotas recuperadas");
  return <>
    <div className="admin-featured-metrics">{featured.map(config => { const metric = metrics.find(item => item.label === config.label); return metric && <article className={`admin-kpi admin-kpi-${config.tone}`} key={config.label}><div className="admin-kpi-top"><span>{config.eyebrow}</span><span className="admin-kpi-icon"><Icon name={config.icon} /></span></div><AdminHeading level={3} label={metric.label} help={adminHelp(metric.label, metric.help)} /><strong>{chartNumber(metric.value)}</strong><p>{metric.help}</p></article>; })}</div>
    {charts && <div className="admin-widget-grid">
      <section className="admin-widget admin-widget-wide"><div className="admin-widget-heading"><div><AdminHeading level={3} label="Registros y publicaciones" /><p>Evolución dentro del período seleccionado.</p></div><Icon name="chart" /></div><TimelineChart points={charts.timeline} unit={charts.timeline_unit} /><p className="admin-widget-footnote">Fecha de creación · datos conservados · horario de Uruguay.</p></section>
      <section className="admin-widget"><div className="admin-widget-heading"><div><AdminHeading level={3} label="Estado de los trabajos" /><p>Trabajos creados en el período.</p></div><Icon name="layers" /></div><DonutChart label="Estado de los trabajos" slices={charts.jobs.map(item => ({ ...item, help: adminHelp(item.label) }))} /></section>
      <section className="admin-widget"><div className="admin-widget-heading"><div><AdminHeading level={3} label="Publicaciones por tipo" /><p>Incluye avisos recuperados, cerrados u ocultos.</p></div><Icon name="paw" /></div><DonutChart label="Publicaciones por tipo" slices={charts.publications.map(item => ({ ...item, help: adminHelp(item.label) }))} />{recovered && <div className="admin-publication-recoveries"><div><span><Icon name="heart" /><AdminLabel label="Mascotas recuperadas" /></span><strong>{chartNumber(recovered.value)}</strong></div><p>{recovered.help}</p></div>}</section>
      <section className="admin-widget"><div className="admin-widget-heading"><div><AdminHeading level={3} label="Correos por tipo" /><p>Mensajes enviados en el período.</p></div><Icon name="mail" /></div><HorizontalBars items={charts.mail_kinds.map(item => { const label = mailLabels[item.label] || item.label; return { ...item, label, help: adminHelp(label, "Mensajes de este tipo aceptados por el servidor de correo en el período.") }; })} empty="Todavía no hay envíos registrados" /></section>
      <section className="admin-widget"><div className="admin-widget-heading"><div><AdminHeading level={3} label="Estado de las cuentas" /><p>Registradas en el período seleccionado.</p></div><Icon name="shield" /></div><div className="admin-account-total"><strong>{chartNumber(charts.accounts.total)}</strong><AdminLabel label="Cuentas registradas" /></div><div className="admin-account-state"><span><i className="admin-legend-dot admin-tone-teal" /><AdminLabel label="Habilitadas" /></span><strong>{chartNumber(charts.accounts.enabled)}</strong></div><div className="admin-account-state"><span><i className="admin-legend-dot admin-tone-coral" /><AdminLabel label="Bloqueadas" /></span><strong>{chartNumber(charts.accounts.blocked)}</strong></div><div className="admin-verification-progress"><div><AdminLabel label="Correo confirmado" /><strong>{chartNumber(charts.accounts.verified)} de {chartNumber(charts.accounts.total)}</strong></div><div role="progressbar" aria-label="Cuentas con correo confirmado" aria-valuemin={0} aria-valuemax={charts.accounts.total || 1} aria-valuenow={charts.accounts.verified} aria-valuetext={`${charts.accounts.verified} de ${charts.accounts.total} cuentas`}><span style={{ width: `${charts.accounts.total ? charts.accounts.verified / charts.accounts.total * 100 : 0}%` }} /></div></div></section>
    </div>}
    <div className="admin-section-heading admin-secondary-heading"><div><AdminHeading level={3} label="Estado de operación" /><p>Detalle de actividad, procesamiento y contactos.</p></div></div>
    <div className="admin-secondary-metrics">{remaining.map(metric => <div className="admin-compact-metric" key={metric.label}><AdminLabel label={metric.label} help={adminHelp(metric.label, metric.help)} /><strong>{chartNumber(metric.value)}</strong><small>{metric.help}</small></div>)}</div>
    <div className="admin-mail-queue-widget"><span className="admin-queue-icon"><Icon name="mail" /></span><div><AdminHeading level={3} label="Cola de correos" /><p><strong>{chartNumber(queue?.pending || 0)}</strong> <AdminLabel label="Pendientes" /> · <strong>{chartNumber(queue?.failed || 0)}</strong> <AdminLabel label="Sin reintentos disponibles" /></p><small>Estado actual de toda la plataforma. Las solicitudes pueden agruparse en un solo mensaje; estas cifras no se limitan por el período.</small></div><button type="button" className="button button-secondary" onClick={onQueue}>Consultar cola <Icon name="arrow" /></button></div>
  </>;
}
