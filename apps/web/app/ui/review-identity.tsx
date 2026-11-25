export function ReviewIdentity({ id, accountName, anonymous, onChange }: {
  id: string; accountName: string; anonymous: boolean; onChange: (anonymous: boolean) => void;
}) {
  return <fieldset className="review-identity-options"><legend>Cómo querés aparecer</legend>
    <label><input type="radio" name={`${id}-identity`} value="anonymous" checked={anonymous} onChange={() => onChange(true)} /><span><strong>Anónimo</strong><span className="field-help">Sin tu nombre ni tu foto de perfil.</span></span></label>
    <label><input type="radio" name={`${id}-identity`} value="account" checked={!anonymous} onChange={() => onChange(false)} /><span><strong>{accountName}</strong><span className="field-help">Tu nombre de cuenta abreviado y tu foto de perfil, si tenés.</span></span></label>
    <p className="field-help">El nombre se toma de tu cuenta. Tu correo no se publica.</p>
  </fieldset>;
}
