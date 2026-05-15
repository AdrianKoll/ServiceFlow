from datetime import datetime
from decimal import Decimal, InvalidOperation

class FormError(ValueError):
    pass

def text(form, name, default=None, required=False, strip=True):
    value = form.get(name, '')
    if value is None:
        value = ''
    value = value.strip() if strip and isinstance(value, str) else value
    if required and not value:
        raise FormError(f'O campo {name} é obrigatório.')
    return value or default

def optional_int(form, name):
    value = text(form, name)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise FormError(f'O campo {name} precisa ser um número válido.')

def optional_decimal(form, name):
    value = text(form, name)
    if value is None:
        return None
    value = value.replace('.', '').replace(',', '.') if isinstance(value, str) and ',' in value else value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise FormError(f'O campo {name} precisa ser um valor válido.')

def optional_datetime(form, name, fmt):
    value = text(form, name)
    if value is None:
        return None
    try:
        return datetime.strptime(value, fmt)
    except (TypeError, ValueError):
        raise FormError(f'O campo {name} precisa estar em uma data válida.')
