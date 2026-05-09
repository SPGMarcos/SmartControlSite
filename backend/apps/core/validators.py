import bleach
from rest_framework import serializers


ALLOWED_TAGS = []
ALLOWED_ATTRIBUTES = {}


def sanitize_text(value):
    if value is None:
        return value
    return bleach.clean(str(value).strip(), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def validate_clean_text(value, field_name="text", max_length=None):
    cleaned = sanitize_text(value)
    if max_length and len(cleaned) > max_length:
        raise serializers.ValidationError({field_name: f"Maximo de {max_length} caracteres."})
    return cleaned
