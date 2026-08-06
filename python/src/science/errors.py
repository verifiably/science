"""The error hierarchy.

Every refusal in this package raises one of these. They are deliberately
fine-grained: several banked oracles turn on refusals staying *distinct* rather
than collapsing into one another (D3's five-way non-collapsing test is the
sharpest case), and a test that can only assert "something was raised" cannot
tell a good refusal from a bad one.
"""


class ScienceError(Exception):
    """Base for every error this package raises."""


class IdentityError(ScienceError):
    """A value or domain was refused by the identity contract."""


class UnsupportedValueType(IdentityError):
    """A value of a type the contract does not admit."""


class NullRefused(IdentityError):
    """A null. Refused, never pruned: an absent member must differ from a
    present-and-empty one, and pruning is what makes ``{"x": null}`` and ``{}``
    the same bytes."""


class BinaryFloatRefused(IdentityError):
    """A binary float. The caller supplies a decimal and owns the rounding, so a
    scientific value never inherits an accidental IEEE spelling."""


class NonFiniteDecimal(IdentityError):
    """``NaN``, ``Infinity``, ``-Infinity`` or a signalling form. JSON has no
    encoding for these and every substitute collides with something else."""


class NonStringKey(IdentityError):
    """An object key that is not a string."""


class KeyCollision(IdentityError):
    """Two object keys that are distinct before NFC normalization and identical
    after it. Rejected, never silently merged."""


class LoneSurrogate(IdentityError):
    """A string carrying an unpaired UTF-16 surrogate. It has no UTF-8 encoding,
    and the two implementations disagree about what it even is."""


class MalformedDomain(IdentityError):
    """A digest domain that is not a well-formed, versioned domain name."""
