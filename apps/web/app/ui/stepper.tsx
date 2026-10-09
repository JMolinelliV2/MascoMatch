import { Icon } from "./pictogram";

export function Stepper({ steps, current }: { steps: readonly string[]; current: number }) {
  return <div className="stepper">
    <ol className="step-list" aria-label="Etapas del reporte">
      {steps.map((title, index) => <li key={title} aria-current={current === index + 1 ? "step" : undefined} className={`step-item ${current === index + 1 ? "step-current" : current > index + 1 ? "step-complete" : ""}`}>
        <span className="step-number" aria-hidden="true">{current > index + 1 ? <Icon name="check" /> : index + 1}</span>
        <span>{title}<span className="sr-only">{current > index + 1 ? ", completado" : ""}</span></span>
      </li>)}
    </ol>
    <progress className="step-progress" value={current} max={steps.length} aria-label={`Paso ${current} de ${steps.length}`} />
  </div>;
}
