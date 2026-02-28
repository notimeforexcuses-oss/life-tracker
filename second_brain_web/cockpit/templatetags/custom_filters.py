from django import template
from datetime import datetime

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def format_health_date(value):
    """Formats YYYY-MM-DD or YYYY-MM-DD HH:MM to MM-DD-YYYY."""
    if not value:
        return ""
    try:
        # Try full datetime first
        if " " in value:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M")
        else:
            dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime("%m-%d-%Y")
    except:
        return value

@register.filter
def multiply(value, arg):
    try:
        return float(value or 0) * float(arg or 0)
    except (ValueError, TypeError):
        return 0.0

@register.filter
def percentage(value, total):
    if not total: return 0
    return (float(value) / float(total)) * 100

@register.filter
def calculate_segments(meal):
    """Calculates SVG dasharray offsets for macro donut chart."""
    total = float(meal.protein_g or 0) + float(meal.carbs_g or 0) + float(meal.fat_g or 0)
    if total == 0:
        return {'p': 0, 'c': 0, 'f': 0, 'p_off': 0, 'c_off': 0, 'f_off': 0}
    
    p_pct = (float(meal.protein_g or 0) / total) * 100
    c_pct = (float(meal.carbs_g or 0) / total) * 100
    f_pct = (float(meal.fat_g or 0) / total) * 100
    
    # 100 units total circumference for simplicity in SVG
    return {
        'p': p_pct,
        'c': c_pct,
        'f': f_pct,
        'p_off': 0,
        'c_off': p_pct,
        'f_off': p_pct + c_pct
    }

@register.filter
def to_hours(minutes):
    if not minutes: return "0m"
    h = minutes // 60
    m = minutes % 60
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"
