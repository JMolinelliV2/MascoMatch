import type { Metadata } from "next";
import { LoginForm } from "./login-form";
import { AuthLayout } from "../ui/auth-layout";

export const metadata: Metadata = { title: "Ingresar — MascoMatch" };

export default function LoginPage() {
  return <AuthLayout mode="login">
    <LoginForm />
  </AuthLayout>;
}
