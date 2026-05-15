from datetime import datetime

def get_initials(name: str) -> str:
    parts = (name or '').split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return (parts[0][:2] if parts else 'SF').upper()

def darken_hex(hex_color: str, amount: float = 0.12) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return '#{:02x}{:02x}{:02x}'.format(max(0, int(r*(1-amount))), max(0, int(g*(1-amount))), max(0, int(b*(1-amount))))

def hex_alpha(hex_color: str, alpha: float = 0.15) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{alpha})'

def fmt_brl(value):
    if value is None: return '-'
    return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def fmt_date(dt):
    if not dt: return '-'
    if isinstance(dt, str): return dt[:10]
    return dt.strftime('%d/%m/%Y')

def fmt_datetime(dt):
    if not dt: return '-'
    if isinstance(dt, str): return dt
    return dt.strftime('%d/%m/%Y %H:%M')
