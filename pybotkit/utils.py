import sys

def django_verification(request, validation_token):
    from django.http import HttpResponse

    if request.GET['hub.verify_token'] == validation_token:
        return HttpResponse(
            request.GET['hub.challenge']
        )
    return HttpResponse('Error, wrong validation token')

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()