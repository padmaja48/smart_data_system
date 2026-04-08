"""
mixins.py - Reusable mixin classes for adding functionality to other classes.
"""

import datetime
import json


class TimestampMixin:
    """Adds created_at and updated_at timestamp tracking."""

    def _init_timestamps(self):
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = self.created_at

    def touch(self):
        """Update the modified timestamp."""
        self.updated_at = datetime.datetime.now().isoformat()

    def age_seconds(self):
        """Get age in seconds since creation."""
        created = datetime.datetime.fromisoformat(self.created_at)
        return (datetime.datetime.now() - created).total_seconds()


class SerializableMixin:
    """Adds ability to serialize objects to/from JSON."""

    def to_dict(self):
        """Convert object to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_')
        }

    def to_json(self):
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary."""
        obj = cls.__new__(cls)
        for key, value in data.items():
            setattr(obj, key, value)
        return obj


class ValidationMixin:
    """Base mixin for adding validation support."""

    _validation_rules = {}

    def validate(self):
        """Run validation rules and return (is_valid, errors_list)."""
        errors = []
        for field, rule in self._validation_rules.items():
            value = getattr(self, field, None)
            ok, msg = rule(value)
            if not ok:
                errors.append(f"{field}: {msg}")
        return len(errors) == 0, errors


class LoggableMixin:
    """Adds logging capability to track events."""

    def _init_log(self):
        self._events = []

    def log_event(self, message):
        self._events.append({
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "event": message
        })

    def get_log(self):
        return list(self._events)
