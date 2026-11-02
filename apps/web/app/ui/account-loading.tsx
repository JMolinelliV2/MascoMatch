import { LoadingState } from "./loading-state";

export function AccountLoading({
  title = "Cargando tu cuenta",
  description = "Enseguida vas a poder continuar.",
  reports = false,
}: { title?: string; description?: string; reports?: boolean }) {
  return <section className={`account-loading${reports ? " account-loading--reports" : ""}`}>
    <LoadingState title={title} description={description} />
    {reports && <div className="account-loading-preview" aria-hidden="true">
      <div className="account-loading-summary"><span /><span /></div>
      <div className="account-loading-case"><span className="account-loading-photo" /><div className="account-loading-lines"><span /><span /><span /></div></div>
    </div>}
  </section>;
}
