import os
import sys
import json

import requests
from flask import Flask, request, send_from_directory
import datetime
from random import randint

import env

from pybotkit import MessengerClient, messages, attachments, templates, elements
from pybotkit.event_handler import EventHandler
from pybotkit.utils import log, convert_timestame

messenger = MessengerClient(access_token=env.PAGE_ACCESS_TOKEN)
# messenger.add_greeting_text("Hi {{user_full_name}}, welcome to this crappy bot!")
# messenger.add_getstarted_button('GET_STARTED')
handler = EventHandler()
# messenger.set_example_persistent_menu()

app = Flask(__name__, static_folder='public')

SERVER_URL = env.SERVER_URL    

@app.route('/assets/<path:path>', methods=['GET'])
def send_assets(path):
    return send_from_directory('public/assets', path)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/webhook', methods=['GET'])
def verify():
    # Source: https://github.com/hartleybrody/fb-messenger-bot/blob/master/app.py
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == env.VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/webhook', methods=['POST'])
def webhook():

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    handler.webhook_handler(data)    

    # // Assume all went well.
    # //
    # // You must send back a 200, within 20 seconds, to let us know you've 
    # // successfully received the callback. Otherwise, the request will time out.                    
    return "ok", 200


@app.route('/authorize', methods=['GET'])
def authorize():
    '''
    * This path is used for account linking. The account linking call-to-action
    * (sendAccountLinking) is pointed to this URL. 
    '''
    account_linking_token = request.args.get("account_linking_token")
    redirect_uri = request.args.get("redirect_uri")

    # Authorization Code should be generated per user by the developer. This will 
    # be passed to the Account Linking callback.
    auth_code = "1234567890"

    # Redirect users to this URI on successful login
    redirect_uri_success = redirect_uri + "&authorization_code=" + auth_code

    return json.dumps({
            "accountLinkingToken": account_linking_token,
            "redirectURI": redirect_uri,
            "redirectURISuccess": redirect_uri_success
        })


def received_authentication(event):     
    ''''
    Authorization Event

    The value for 'optin.ref' is defined in the entry point. For the "Send to 
    Messenger" plugin, it is the 'data-ref' field. Read more at 
    https://developers.facebook.com/docs/messenger-platform/webhook-reference/authentication     
    '''
    sender_id = event["sender"]["id"]
    recipient_id = event["recipient"]["id"]
    time_of_auth = event["timestamp"]

    # The 'ref' field is set in the 'Send to Messenger' plugin, in the 'data-ref'
    # The developer can set this to an arbitrary value to associate the 
    # authentication callback with the 'Send to Messenger' click event. This is
    # way to do account linking when the user clicks the 'Send to Messenger' 
    # lugin.    
    pass_through_param = event["optin"]["ref"]

    log("Received authentication for user {sender} and page {page} with pass through param {param} at {time}".format(
            sender=sender_id,
            page=recipient_id,
            param=pass_through_param,
            time=time_of_auth
        ))

    # When an authentication is received, we'll send a message back to the sender
    # to let them know it was successful.    
    send_text_message(sender_id, "Authentication successful")


@handler.hears('hehe')
def send_huehue(event):
    sender_id = event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient = messages.Recipient(recipient_id=sender_id)        

    message_text = 'huehue'
    message = messages.Message(text=message_text)
    request = messages.MessageRequest(recipient, message)

    messenger.send(request)

@handler.on_postback('DEVELOPER_DEFINED_PAYLOAD_FOR_HELP')
def help(event):
    sender_id = event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient = messages.Recipient(recipient_id=sender_id)        

    message_text = "Here's your help"
    message = messages.Message(text=message_text)
    request = messages.MessageRequest(recipient, message)

    messenger.send(request)

@handler.on_attachment(EventHandler.ATM_LOCATION)
def get_location(attachment, event):
    log('get location, with attachment: {attachment}'.format(attachment=attachment))    
    
    sender_id = event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient = messages.Recipient(recipient_id=sender_id)            

    lat = attachment.get("payload").get("coordinates").get("lat")
    long = attachment.get("payload").get("coordinates").get("long")
    message_text = "Your location: lat: {lat}, and long: {long}".format(lat=lat, long=long)
    message = messages.Message(text=message_text)
    request = messages.MessageRequest(recipient, message)

    messenger.send(request)    

# @handler.on_event(EventHandler.EVENT_MESSAGE)
def receive_message(event):
    '''
    * Message Event
    *
    * This event is called when a message is sent to your page. The 'message' 
    * object format can vary depending on the kind of message that was received.
    * Read more at https://developers.facebook.com/docs/messenger-platform/webhook-reference/message-received
    *
    * For this example, we're going to echo any text that we get. If we get some 
    * special keywords ('button', 'generic', 'receipt'), then we'll send back
    * examples of those bubbles to illustrate the special message bubbles we've 
    * created. If we receive a message with an attachment (image, video, audio), 
    * then we'll simply confirm that we've received the attachment.    
    '''    

    # log('message event data: ', event)
    sender_id = event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient_id = event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID    
    time_of_message = event["timestamp"]
    time_converted = convert_timestame(time_of_message)
    message = event["message"]

    recipient = messages.Recipient(recipient_id=sender_id)        

    log("Received message for user {sender_id} and page {recipient_id} at {time} with message:".format(sender_id=sender_id, recipient_id=recipient_id, time=time_of_message))
    log(message)    

    is_echo = message.get("is_echo")    
    message_id = message.get("mid")
    app_id = message.get("app_id")
    metadata = message.get("metadata")

    message_text = message.get("text")
    message_attachments = message.get("attachments")
    quick_reply = message.get("quick_reply")

    if is_echo:
        log("Received echo for message {message_id} and app {app_id} with metadata {metadata}".format(
                message_id = message_id, 
                app_id = app_id, 
                metadata = metadata
            ))
        return
    elif quick_reply:
        quick_reply_payload = quick_reply["payload"]
        log("Quick reply for message {message_id} with payload {payload}".format(
                message_id=message_id,
                payload=quick_reply_payload
            ))
        # send_text_message(sender_id, "Quick reply tapped")
        message = messages.Message(text='Quick reply tapped')
        request = messages.MessageRequest(recipient, message)

        messenger.send(request)
        return

    # If we receive a text message, check to see if it matches a keyword
    # and send back the example. Otherwise, just echo the text we received.
    if message_text:
        if message_text == 'image':
            send_image_message(sender_id)
        elif message_text == 'giff':
            send_giff_message(sender_id)
        elif message_text == 'audio':
            send_audio_message(sender_id)
        elif message_text == 'video':
            send_video_message(sender_id)
        elif message_text == 'file':
            send_file_message(sender_id)
        elif message_text == 'button':
            send_button_message(sender_id)
        elif message_text == 'generic':
            send_generic_message(sender_id)
        elif message_text == 'receipt':
            send_receipt_message(sender_id)
        elif message_text == 'quick reply':
            send_quick_reply(sender_id)
        elif message_text == 'read receipt':
            send_read_receipt(sender_id)
        elif message_text == 'typing on':
            send_typing_on(sender_id)
        elif message_text == 'typing off':
            send_typing_off(sender_id)
        elif message_text == 'account linking':
            send_account_linking(sender_id)
        else:
            # send_text_message(sender_id, message_text)
            message = messages.Message(text=message_text)
            request = messages.MessageRequest(recipient, message)

            messenger.send(request)
    elif message_attachments:
        # send_text_message(sender_id, "Message with attachment received")        
        message = messages.Message(text='Message with attachment received')
        request = messages.MessageRequest(recipient, message)

        messenger.send(request)

def send_image_message(recipient_id):
    '''
    Send an image using the Send API.
    '''
    # url = SERVER_URL + "/assets/rift.png"
    url = "http://messengerdemo.parseapp.com/img/rift.png"
    log("url is {url}".format(url=url))

    recipient = messages.Recipient(recipient_id=recipient_id)
    attachment = attachments.ImageAttachment(url=url)
    message = messages.Message(attachment=attachment)
    request = messages.MessageRequest(recipient, message)

    messenger.send(request)

def send_giff_message(recipient_id):
    '''
    Send a Gif using the Send API.
    '''
    url = SERVER_URL + "/assets/instagram_logo.gif"

    recipient = messages.Recipient(recipient_id=recipient_id)
    attachment = attachments.ImageAttachment(url=url)
    message = messages.Message(attachment=attachment)
    request = messages.MessageRequest(recipient, message)

    messenger.send(request)

def send_audio_message(recipient_id):
    '''
    Send audio using the Send API.
    '''
    url = SERVER_URL + "/assets/sample.mp3"

    recipient = messages.Recipient(recipient_id=recipient_id)
    attachment = attachments.AudioAttachment(url=url)
    message = messages.Message(attachment=attachment)
    request = messages.MessageRequest(recipient, message)

    messenger.send(request)

def send_video_message(recipient_id):
    '''
    Send a video using the Send API.
    '''
    url = SERVER_URL + "/assets/allofus480.mov"

    recipient = messages.Recipient(recipient_id=recipient_id)
    attachment = attachments.VideoAttachment(url=url)
    message = messages.Message(attachment=attachment)
    request = messages.MessageRequest(recipient, message)

    messenger.send(request)

def send_file_message(recipient_id):
    '''
    Send a file using the Send API.
    '''
    url = SERVER_URL + "/assets/test.txt"

    recipient = messages.Recipient(recipient_id=recipient_id)
    attachment = attachments.FileAttachment(url=url)
    message = messages.Message(attachment=attachment)
    request = messages.MessageRequest(recipient, message)

    messenger.send(request)

def send_button_message(recipient_id):
    '''
    Send a button message using the Send API.
    '''
    recipient = messages.Recipient(recipient_id=recipient_id)

    web_button = elements.WebUrlButton(
       title='Open Web URL',
       url='https://www.oculus.com/en-us/rift/'
    )
    postback_button = elements.PostbackButton(
       title='Trigger Postback',
       payload='DEVELOPER_DEFINED_PAYLOAD'
    )
    phone_number_button = elements.PhoneNumberButton(
        title='Call Phone Number',
        payload='+16505551234'
    )
    template = templates.ButtonTemplate(
       text='This is test text',
       buttons=[
           web_button, postback_button, phone_number_button
       ]
    )

    attachment = attachments.TemplateAttachment(template=template)
    message = messages.Message(attachment=attachment)
    request = messages.MessageRequest(recipient, message)

    messenger.send(request)    


if __name__ == '__main__':        
    app.run(debug=True)    