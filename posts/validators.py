from django.core.exceptions import ValidationError


def validate_not_empty(value):
    if not value:
        raise ValidationError(
            'А кто поле будет заполнять, Пушкин?',
            params={'value': value},
        )
