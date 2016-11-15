import sys
from wit import Wit

if len(sys.argv) != 2:
    print('usage: python ' + sys.argv[0] + ' <wit-token>')
    exit(1)
access_token = sys.argv[1]

# Quickstart example
# See https://wit.ai/ar7hur/Quickstart

def first_entity_value(entities, entity):
    if entity not in entities:
        return None
    val = entities[entity][0]['value']
    if not val:
        return None
    return val['value'] if isinstance(val, dict) else val

def send(request, response):
    print(response['text'])

def get_forecast(request):
    context = request['context']
    entities = request['entities']

    print(context)
    print(entities)
    loc = first_entity_value(entities, 'location')
    if loc:
        context['location'] = loc
        context['forecast'] = 'sunny'
    else:
        context['missingLocation'] = True
        if context.get('forecast') is not None:
            del context['forecast']

    return context

def clear_context(request):
    context = request['context']
    context = {}
    entities = request['entities']
    entities = {}

    return context

def update_context(request, *args, **kwargs):
    context = request['context']
    entities = request['entities']

    print('checking merge')
    print(request)
    print('-----')
    print(args)
    print(kwargs)

    name = first_entity_value(entities, 'name')    
    if name:        
        context['name_user'] = name
        if context.get('missingName') is not None:
            del context['missingName']
    else:
        context['missingName'] = True

    return context

    

actions = {
    'send': send,
    'getForecast': get_forecast,
    'clearContext': clear_context,
    'updateContext': update_context,
    # 'merge': update_context,
}

client = Wit(access_token=access_token, actions=actions)
client.interactive()
