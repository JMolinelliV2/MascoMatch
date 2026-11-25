import { parsePhoneNumberFromString } from "libphonenumber-js/max";

export const PHONE_ERROR = "Ingresá un teléfono válido. Para Uruguay, por ejemplo 099 123 456; para otros países, incluí + y el código de país.";
export const PHONE_HELP = "Uruguay: 099 123 456 o +598 99 123 456. Otros países: incluí + y el código de país.";

export function phoneError(value: string, required = false): string {
  const phone = value.trim().replace(/\s+/g, " ");
  if (!phone) return required ? "Ingresá un teléfono de contacto." : "";
  if (phone.length > 32 || !/^\+?[0-9 ().-]+$/.test(phone)) return PHONE_ERROR;
  const parsed = parsePhoneNumberFromString(phone, { defaultCountry: "UY", extract: false });
  return parsed?.isValid() && !parsed.ext ? "" : PHONE_ERROR;
}
