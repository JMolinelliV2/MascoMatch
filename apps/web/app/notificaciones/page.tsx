import type { Metadata } from "next";
import { NotificationsInbox } from "./notifications-inbox";

export const metadata: Metadata = { title: "Notificaciones — PetMatch" };
export default async function NotificationsPage({ searchParams }: { searchParams: Promise<{ aviso?: string | string[] }> }) {
  const { aviso } = await searchParams;
  return <NotificationsInbox selectedId={typeof aviso === "string" ? aviso : undefined} />;
}
