import { Icon } from "./pictogram";

export function AccountLoading({
  title = "Preparando tu cuenta",
  description = "Enseguida vas a poder continuar.",
  reports = false,
}: { title?: string; description?: string; reports?: boolean }) {
  return <section className={`account-loading${reports ? " account-loading--reports" : ""}`}>
    <div className="account-loading-message" role="status" aria-live="polite" aria-atomic="true">
      <span className="account-loading-mark" aria-hidden="true"><Icon name="paw" /><span className="account-loading-ring" /></span>
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
    {reports && <div className="account-loading-preview" aria-hidden="true">
      <div className="account-loading-summary"><span /><span /></div>
      <div className="account-loading-case"><span className="account-loading-photo" /><div className="account-loading-lines"><span /><span /><span /></div></div>
    </div>}
  </section>;
}
