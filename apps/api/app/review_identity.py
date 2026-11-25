"""Public review identity is derived from the account, never supplied as an alias."""


def abbreviated_name(name: str) -> str:
    words = name.split()
    if not words:
        return "Usuario de MascoMatch"
    first = words[0][:76]
    initial = next((char.upper() for char in words[1] if char.isalpha()), "") if len(words) > 1 else ""
    return f"{first} {initial}." if initial else first
