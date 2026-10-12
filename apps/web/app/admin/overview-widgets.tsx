"use client";
import { Icon } from "../ui/pictogram";
import type { IconName } from "../ui/pictogram";
import { chartNumber, DonutChart, HorizontalBars, TimelineChart } from "./dashboard-charts";
import type { ChartSlice, TimelinePoint } from "./dashboard-charts";
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
  return <>
    <div className="admin-featured-metrics">{featured.map(config => { const metric = metrics.find(item => item.label === config.label); return metric && <article className={`admin-kpi admin-kpi-${config.tone}`} key={config.label}><div className="admin-kpi-top"><span>{config.eyebrow}</span><span className="admin-kpi-icon"><Icon name={config.icon} /></span></div><h3>{metric.label}</h3><strong>{chartNumber(metric.value)}</strong><p>{metric.help}</p></article>; })}</div>
    {charts && <div className="admin-widget-grid">
      <section className="admin-widget admin-widget-wide"><div className="admin-widget-heading"><div><h3>Registros y publicaciones</h3><p>Evolución dentro del período seleccionado.</p></div><Icon name="chart" /></div><TimelineChart points={charts.timeline} unit={charts.timeline_unit} /><p className="admin-widget-footnote">Fecha de creación · datos conservados · horario de Uruguay.</p></section>
      <section className="admin-widget"><div className="admin-widget-heading"><div><h3>Estado de los trabajos</h3><p>Trabajos creados en el período.</p></div><Icon name="layers" /></div><DonutChart label="Estado de los trabajos" slices={charts.jobs} /></section>
      <section className="admin-widget"><div className="admin-widget-heading"><div><h3>Publicaciones por tipo</h3><p>Incluye avisos cerrados u ocultos.</p></div><Icon name="paw" /></div><DonutChart label="Publicaciones por tipo" slices={charts.publications} /></section>
      <section className="admin-widget"><div className="admin-widget-heading"><div><h3>Correos por tipo</h3><p>Mensajes enviados en el período.</p></div><Icon name="mail" /></div><HorizontalBars items={charts.mail_kinds.map(item => ({ ...item, label: mailLabels[item.label] || item.label }))} empty="Todavía no hay envíos registrados" /></section>
      <section className="admin-widget"><div className="admin-widget-heading"><div><h3>Estado de las cuentas</h3><p>Registradas en el período seleccionado.</p></div><Icon name="shield" /></div><div className="admin-account-total"><strong>{chartNumber(charts.accounts.total)}</strong><span>Cuentas registradas</span></div><div className="admin-account-state"><span><i className="admin-legend-dot admin-tone-teal" />Habilitadas</span><strong>{chartNumber(charts.accounts.enabled)}</strong></div><div className="admin-account-state"><span><i className="admin-legend-dot admin-tone-coral" />Bloqueadas</span><strong>{chartNumber(charts.accounts.blocked)}</strong></div><div className="admin-verification-progress"><div><span>Correo confirmado</span><strong>{chartNumber(charts.accounts.verified)} de {chartNumber(charts.accounts.total)}</strong></div><div role="progressbar" aria-label="Cuentas con correo confirmado" aria-valuemin={0} aria-valuemax={charts.accounts.total || 1} aria-valuenow={charts.accounts.verified} aria-valuetext={`${charts.accounts.verified} de ${charts.accounts.total} cuentas`}><span style={{ width: `${charts.accounts.total ? charts.accounts.verified / charts.accounts.total * 100 : 0}%` }} /></div></div></section>
    </div>}
    <div className="admin-section-heading admin-secondary-heading"><div><h3>Estado de operación</h3><p>Detalle de actividad, procesamiento y contactos.</p></div></div>
    <div className="admin-secondary-metrics">{remaining.map(metric => <div className="admin-compact-metric" key={metric.label}><span>{metric.label}</span><strong>{chartNumber(metric.value)}</strong><small>{metric.help}</small></div>)}</div>
    <div className="admin-mail-queue-widget"><span className="admin-queue-icon"><Icon name="mail" /></span><div><h3>Cola de correos</h3><p><strong>{chartNumber(queue?.pending || 0)}</strong> pendientes · <strong>{chartNumber(queue?.failed || 0)}</strong> sin reintentos disponibles.</p><small>Estado actual de toda la plataforma. Las solicitudes pueden agruparse en un solo mensaje; estas cifras no se limitan por el período.</small></div><button type="button" className="button button-secondary" onClick={onQueue}>Consultar cola <Icon name="arrow" /></button></div>
  </>;
}
