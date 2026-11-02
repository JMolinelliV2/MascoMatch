import { LoadingState } from "./ui/loading-state";

export default function Loading() {
  return <main id="main-content" className="page route-loading"><LoadingState title="Cargando la página" description="Estamos preparando lo que necesitás." /></main>;
}
