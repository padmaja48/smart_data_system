"""
validation.py - Regex-based input validation.
"""

import re
from abc import ABC, abstractmethod
from utils.mixins import ValidationMixin, LoggableMixin


# Compiled regex patterns for validation
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z\s\-']{1,49}$")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PHONE_PATTERN = re.compile(r"^(\+?[0-9]{1,3}[\s\-]?)?(\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{4}$")
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&\-_#^])[A-Za-z\d@$!%*?&\-_#^]{8,}$")


class BaseValidator(ABC):
    """Abstract base class for validators."""

    @abstractmethod
    def validate(self, value: str) -> tuple[bool, str]:
        """Returns (is_valid, message)."""
        pass

    def is_valid(self, value: str) -> bool:
        ok, _ = self.validate(value)
        return ok


class NameValidator(BaseValidator):
    def validate(self, value: str):
        if not value or not value.strip():
            return False, "Name cannot be empty"
        if not NAME_PATTERN.match(value.strip()):
            return False, "Name must be 2–50 letters (spaces and hyphens allowed)"
        return True, "Valid"


class EmailValidator(BaseValidator):
    def validate(self, value: str):
        if not value:
            return False, "Email cannot be empty"
        if not EMAIL_PATTERN.match(value.strip()):
            return False, "Invalid email format (e.g. user@example.com)"
        return True, "Valid"


class PhoneValidator(BaseValidator):
    def validate(self, value: str):
        if not value:
            return False, "Phone cannot be empty"
        cleaned = re.sub(r"[\s\-\(\)]", "", value.strip())
        if len(cleaned) < 7 or len(cleaned) > 15:
            return False, "Phone number must be 7–15 digits"
        if not re.match(r"^\+?[0-9]+$", cleaned):
            return False, "Phone must contain digits only (with optional +, -, spaces)"
        return True, "Valid"


class PasswordValidator(BaseValidator):
    def validate(self, value: str):
        if not value:
            return False, "Password cannot be empty"
        if len(value) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r"[A-Z]", value):
            return False, "Password needs at least one uppercase letter"
        if not re.search(r"[a-z]", value):
            return False, "Password needs at least one lowercase letter"
        if not re.search(r"\d", value):
            return False, "Password needs at least one digit"
        if not re.search(r"[@$!%*?&\-_#^]", value):
            return False, "Password needs at least one special character (@$!%*?&-_#^)"
        return True, "Valid"


class FormValidator(ValidationMixin, LoggableMixin):
    """Validates form submissions using all field validators."""

    def __init__(self):
        self._init_log()
        self._name_v = NameValidator()
        self._email_v = EmailValidator()
        self._phone_v = PhoneValidator()
        self._password_v = PasswordValidator()

    def validate_form(self, name, email, phone, password):
        """Validate all form fields and return results."""
        results = {}
        all_valid = True
        
        # Validate each field
        for field, value, validator in [
            ('name', name, self._name_v),
            ('email', email, self._email_v),
            ('phone', phone, self._phone_v),
            ('password', password, self._password_v)
        ]:
            ok, msg = validator.validate(value)
            results[field] = {
                'valid': ok,
                'message': msg
            }
            if not ok:
                all_valid = False
            self.log_event(f"Validated {field}: {'OK' if ok else msg}")
        
        return all_valid, results
