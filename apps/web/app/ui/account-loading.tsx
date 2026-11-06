import { LoadingState } from "./loading-state";

export function AccountLoading({
  title = "Cargando tu cuenta",
  description = "Enseguida vas a poder continuar.",
}: { title?: string; description?: string; reports?: boolean }) {
  return <LoadingState title={title} description={description} />;
}
