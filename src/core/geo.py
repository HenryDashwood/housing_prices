"""Geographic code utilities for handling LA codes, TTWAs, and MSAs."""

from typing import Literal

# Country type alias
Country = Literal["uk", "us"]

# UK Local Authority code prefixes
UK_LA_PREFIXES = {
    "E06": "Unitary Authority (England)",
    "E07": "Non-metropolitan District",
    "E08": "Metropolitan District",
    "E09": "London Borough",
    "W06": "Unitary Authority (Wales)",
    "S12": "Council Area (Scotland)",
    "N09": "Local Government District (NI)",
}


def is_uk_local_authority(code: str) -> bool:
    """
    Check if a code is a UK local authority code.

    Args:
        code: Geographic code to check

    Returns:
        True if code is a UK LA code
    """
    if not code or len(code) < 3:
        return False
    prefix = code[:3]
    return prefix in UK_LA_PREFIXES


def is_england_wales_la(code: str) -> bool:
    """
    Check if a code is an England or Wales local authority.

    Args:
        code: Geographic code to check

    Returns:
        True if code is an England/Wales LA code
    """
    if not code or len(code) < 3:
        return False
    prefix = code[:3]
    return prefix in ("E06", "E07", "E08", "E09", "W06")


def get_la_type(code: str) -> str | None:
    """
    Get the type of local authority from its code.

    Args:
        code: LA code

    Returns:
        LA type description or None if not recognised
    """
    if not code or len(code) < 3:
        return None
    return UK_LA_PREFIXES.get(code[:3])


# Known LA code corrections (ONS data sometimes has typos)
UK_LA_CODE_FIXES = {
    "E08000039": "E08000019",  # Sheffield (typo in ONS data)
    "E08000038": "E08000016",  # Barnsley (typo in ONS data)
}


def fix_la_code(code: str) -> str:
    """
    Apply known LA code corrections.

    Args:
        code: LA code to fix

    Returns:
        Corrected LA code
    """
    return UK_LA_CODE_FIXES.get(code, code)
