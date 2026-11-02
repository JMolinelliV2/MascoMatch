import type { Metadata } from "next";
import { RegistrationForm } from "./registration-form";
import { AuthLayout } from "../ui/auth-layout";

export const metadata: Metadata = { title: "Crear cuenta — MascoMatch" };

export default function CreateAccountPage() {
  return <AuthLayout mode="register">
    <RegistrationForm />
  </AuthLayout>;
}
