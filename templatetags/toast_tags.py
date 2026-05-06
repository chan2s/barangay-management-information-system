from django import template
from django.contrib.messages import get_messages
import json

register = template.Library()

@register.simple_tag(takes_context=True)
def messages_json(context):
    """Convert Django messages to JSON for JavaScript toasts"""
    request = context.get('request')
    if not request:
        return '[]'
    
    messages = []
    for message in get_messages(request):
        messages.append({
            'message': str(message),
            'tags': message.tags.split()[0] if message.tags else 'info'
        })
    
    return json.dumps(messages)