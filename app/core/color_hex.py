import re


HEX_PATTERN = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def is_valid_hex(hex_str: str) -> bool:
    return bool(HEX_PATTERN.fullmatch(hex_str.strip()))


def normalize_hex(hex_str: str) -> str:
    value = hex_str.strip().lstrip("#")

    if not is_valid_hex(value):
        raise ValueError(f"Invalid hex color: {hex_str}")

    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)

    return f"#{value.lower()}"


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    normalized = normalize_hex(hex_str)
    value = normalized[1:]
    return tuple(int(value[i : i + 2], 16) for i in range(0, 6, 2))
