"""Cryptographically secure random password generation and entropy math.

Uses only :mod:`secrets` / :mod:`random.SystemRandom` from the standard
library.  Generated passwords include at least one character from every
enabled character class (when the requested length allows it).
"""

from __future__ import annotations

import math
import secrets
import string

UPPER = string.ascii_uppercase
LOWER = string.ascii_lowercase
DIGITS = string.digits
SYMBOLS = string.punctuation
AMBIGUOUS = "0O1lI|`'\";:.,[]{}()/\\<>"

_shuffle = secrets.SystemRandom().shuffle


def _pool(
    use_upper: bool,
    use_lower: bool,
    use_digits: bool,
    use_symbols: bool,
    exclude_ambiguous: bool,
) -> tuple[list[tuple[str, str]], str]:
    """Return ``[(label, chars), ...]`` for enabled classes and the full pool."""
    classes: list[tuple[str, str]] = []
    if use_upper:
        classes.append(("upper", UPPER))
    if use_lower:
        classes.append(("lower", LOWER))
    if use_digits:
        classes.append(("digits", DIGITS))
    if use_symbols:
        classes.append(("symbols", SYMBOLS))

    if exclude_ambiguous:
        classes = [(label, "".join(c for c in chars if c not in AMBIGUOUS))
                   for label, chars in classes]
        classes = [(label, chars) for label, chars in classes if chars]

    full = "".join(chars for _label, chars in classes)
    return classes, full


def generate(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
    exclude_ambiguous: bool = True,
) -> str:
    """Generate a random password of exactly *length* characters.

    Raises ``ValueError`` when *length* is not positive or when no character
    class is enabled.  One character from each enabled class is guaranteed
    when ``length`` is at least the number of classes; the remainder is drawn
    uniformly from the combined pool.  The result is shuffled.
    """
    if isinstance(length, bool) or not isinstance(length, int) or length <= 0:
        raise ValueError("length must be a positive integer")

    classes, full = _pool(
        use_upper, use_lower, use_digits, use_symbols, exclude_ambiguous
    )
    if not full:
        raise ValueError("at least one character class must be enabled")

    chars: list[str] = [secrets.choice(pool) for _label, pool in classes]
    if len(chars) > length:
        chars = chars[:length]
    chars.extend(secrets.choice(full) for _ in range(length - len(chars)))
    _shuffle(chars)
    return "".join(chars)


def estimate_entropy(length: int, pool_size: int) -> float:
    """Return the Shannon entropy (in bits) of a *length*-char password.

    Entropy is ``length * log2(pool_size)``.  Non-positive lengths or pool
    sizes of 1 or less yield ``0.0``.  The result is a ``float``.
    """
    if isinstance(length, bool) or isinstance(pool_size, bool):
        return 0.0
    try:
        length_i = int(length)
        pool_i = int(pool_size)
    except (TypeError, ValueError):
        return 0.0
    if length_i <= 0 or pool_i <= 1:
        return 0.0
    return float(length_i * math.log2(pool_i))
