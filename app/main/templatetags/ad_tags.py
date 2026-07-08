from django import template
from django.db.models.fields.files import FieldFile

register = template.Library()

@register.filter
def img_url(ad, index):
    try:
        img = getattr(ad, f'image_{index}')
        if img and img.name:
            return img.url
    except (ValueError, FileNotFoundError, OSError):
        pass
    return ''

@register.filter
def has_img(ad, index):
    try:
        img = getattr(ad, f'image_{index}')
        if img and img.name:
            return True
    except (ValueError, FileNotFoundError, OSError):
        pass
    return False
