import type { Metadata } from "next";
import { LoginForm } from "./login-form";
import { AuthLayout } from "../ui/auth-layout";

export const metadata: Metadata = { title: "Ingresar — MascoMatch" };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ next?: string | string[] }> }) {
  const { next } = await searchParams;
  return <AuthLayout mode="login">
    <LoginForm returnTo={typeof next === "string" ? next : undefined} />
  </AuthLayout>;
}
