"""The consumer's acquisition limits, stored with each set on creation."""

from dataclasses import dataclass, fields

from science.refusal import Refusal, Refused

__all__ = ["AcquisitionBounds"]


@dataclass(frozen=True)
class AcquisitionBounds:
    max_response_bytes: int = 64 * 1024**2
    max_total_bytes: int = 4 * 1024**3
    max_requests: int = 20_000
    attempts: int = 3
    min_interval_ms: int = 1_000
    backoff_ms: int = 1_000

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            minimum = 0 if field.name in ("min_interval_ms", "backoff_ms") else 1
            if type(value) is not int or value < minimum:
                raise Refused(Refusal("invalid-input", f"acquire {field.name} must be an integer >= {minimum}"))

    @classmethod
    def from_mapping(cls, value: object):
        if not isinstance(value, dict) or value.keys() - {field.name for field in fields(cls)}:
            raise Refused(Refusal("invalid-input", "acquire must be a table of named acquisition bounds"))
        return cls(**value)
