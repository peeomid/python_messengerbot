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
from pybotkit.utils import log

messenger = MessengerClient(access_token=env.PAGE_ACCESS_TOKEN)
# messenger.add_greeting_text("Hi {{user_full_name}}, welcome to this crappy bot!")
# messenger.add_getstarted_button('GET_STARTED')
messenger_handler = EventHandler()
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

    # if data["object"] == "page":

    #     for entry in data["entry"]:
    #         page_id = entry["id"]
    #         time_of_event = entry["time"]

    #         for messaging_event in entry["messaging"]:

    #             if messaging_event.get("optin"):    # optin confirmation
    #                 received_authentication(messaging_event)

    #             elif messaging_event.get("message"):  # someone sent us a message
    #                 receive_message(messaging_event)
                    
    #             elif messaging_event.get("delivery"):  # delivery confirmation
    #                 receive_delivery_confirmation(messaging_event)
                
    #             elif messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
    #                 receive_postback(messaging_event)

    #             elif messaging_event.get("read"):
    #                 receive_message_read(messaging_event)

    #             elif messaging_event.get("account_linking"):
    #                 receive_account_link(messaging_event)
    #             else:
    #                 log("Unknown event received: {event} ".format(event=messaging_event))
    messenger_handler.webhook_handler(data)    

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
        send_text_message(sender_id, "Quick reply tapped")
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
            send_text_message(sender_id, message_text)
    elif message_attachments:
        send_text_message(sender_id, "Message with attachment received")        

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

    # call_send_API(message_data)

def send_receipt_message(recipient_id):
    '''
    Send a receipt message using the Send API.
    '''
    # Generate a random receipt ID as the API requires a unique ID
    receipt_id = "order " + str(randint(0, 1000))

    message_data = json.dumps({
            "recipient": {
                "id": recipient_id
                },
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                      "template_type": "receipt",
                      "recipient_name": "Peter Chang",
                      "order_number": receipt_id,
                      "currency": "USD",
                      "payment_method": "Visa 1234",        
                      "timestamp": "1428444852", 
                      "elements": [{
                        "title": "Oculus Rift",
                        "subtitle": "Includes: headset, sensor, remote",
                        "quantity": 1,
                        "price": 599.00,
                        "currency": "USD",
                        "image_url": SERVER_URL + "/assets/riftsq.png"
                      }, {
                        "title": "Samsung Gear VR",
                        "subtitle": "Frost White",
                        "quantity": 1,
                        "price": 99.99,
                        "currency": "USD",
                        "image_url": SERVER_URL + "/assets/gearvrsq.png"
                      }],
                      "address": {
                        "street_1": "1 Hacker Way",
                        "street_2": "",
                        "city": "Menlo Park",
                        "postal_code": "94025",
                        "state": "CA",
                        "country": "US"
                      },
                      "summary": {
                        "subtotal": 698.99,
                        "shipping_cost": 20.00,
                        "total_tax": 57.67,
                        "total_cost": 626.66
                      },
                      "adjustments": [{
                        "name": "New Customer Discount",
                        "amount": -50
                      }, {
                        "name": "$100 Off Coupon",
                        "amount": -100
                      }]
                    }
                  }
            }
        })

    call_send_API(message_data)

def send_quick_reply(recipient_id):
    '''
    Send a message with Quick Reply buttons.
    '''
    recipient = messages.Recipient(recipient_id=recipient_id)
    postback1_reply = elements.TextQuickReply(
       title='Action',
       payload='DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_ACTION'
    )
    postback2_reply = elements.TextQuickReply(
       title='Comedy',
       payload='DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_COMEDY'
    )
    postback3_reply = elements.TextQuickReply(
       title='Drama',
       payload='DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_DRAMA'
    )
    quick_replies = templates.QuickReplyTemplate(       
       quick_replies=[
           postback1_reply, postback2_reply, postback3_reply
       ]
    )
    
    message = messages.Message(text="What's your favorite movie genre?", quick_replies=quick_replies)
    request = messages.MessageRequest(recipient, message)
    log("data being sent {request}".format(request=request.serialise()))

    messenger.send(request)

def send_read_receipt(recipient_id):
    '''
    Send a read receipt to indicate the message has been read
    '''
    log("Sending a read receipt to mark message as seen")
    recipient = messages.Recipient(recipient_id=recipient_id)
    request = messages.SenderActionRequest(recipient, action=SenderActionRequest.SO_MARK_SEEN)

    messenger.send(request)

    # message_data = json.dumps({
    #         "recipient": {
    #             "id": recipient_id
    #             },
    #         "sender_action": "mark_seen"
    #     })

    # call_send_API(message_data)

def send_typing_on(recipient_id):
    '''
    Turn typing indicator on
    '''
    log("Turning typing indicator on")
    recipient = messages.Recipient(recipient_id=recipient_id)
    request = messages.SenderActionRequest(recipient, action=SenderActionRequest.SO_TYPE_ON)

    messenger.send(request)

def send_typing_off(recipient_id):
    '''
    Turn typing indicator off
    '''
    log("Turning typing indicator off")
    recipient = messages.Recipient(recipient_id=recipient_id)
    request = messages.SenderActionRequest(recipient, action=SenderActionRequest.SO_TYPE_OFF)

    messenger.send(request)


def send_account_linking(recipient_id):
    '''
    Send a message with the account linking call-to-action
    '''
    message_data = json.dumps({
            "recipient": {
                "id": recipient_id
                },
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                      "template_type": "button",
                      "text": "Welcome. Link your account.",
                      "buttons":[{
                        "type": "account_link",
                        "url": SERVER_URL + "/authorize"
                      }]
                    }
                  }
            }
        })

    call_send_API(message_data)


def receive_delivery_confirmation(event):
    '''
    * Delivery Confirmation Event
    *
    * This event is sent to confirm the delivery of a message. Read more about 
    * these fields at https://developers.facebook.com/docs/messenger-platform/webhook-reference/message-delivered
    '''
    sender_id = event["sender"]["id"]
    recipient_id = event["recipient"]["id"]
    delivery = event["delivery"]
    message_ids = delivery.get("mids")
    watermark = delivery["watermark"]
    sequence_number = delivery["seq"]

    if message_ids:
        for message_id in message_ids:
            log("Received delivery confirmation for message ID: {message}".format(message=message_id))

    log("All message before {watermark} were delivered.".format(watermark=watermark))

def receive_message_read(event):
    '''
    * Message Read Event
    *
    * This event is called when a previously-sent message has been read.
    * https://developers.facebook.com/docs/messenger-platform/webhook-reference/message-read
    '''
    sender_id = event["sender"]["id"]
    recipient_id = event["recipient"]["id"]

    # All messages before watermark (a timestamp) or sequence have been seen.
    watermark = event["read"]["watermark"]
    sequence_number = event["read"]["seq"]

    log("Received message read event for watermark {watermark} and sequence number {number}".format(
        watermark=watermark, number=sequence_number))

def receive_account_link(event):
    '''
    * Account Link Event
    *
    * This event is called when the Link Account or UnLink Account action has been
    * tapped.
    * https://developers.facebook.com/docs/messenger-platform/webhook-reference/account-linking
    '''
    sender_id = event["sender"]["id"]
    recipient_id = event["recipient"]["id"]

    status = event["account_linking"]["status"]
    auth_code = event["account_linking"]["authorization_code"]

    log("Received account link event with for user {sender} with status {status} and auth code {code} ".format(
        sender=senderID, status=status, code=authCode))

def send_generic_message(recipient_id):
    # Send a Structured Message (Generic Message type) using the Send API.
    recipient = messages.Recipient(recipient_id=recipient_id)

    rift_web_button = elements.WebUrlButton(
       title='Open Web URL',
       url='https://www.oculus.com/en-us/rift/'
    )
    rift_postback_button = elements.PostbackButton(
        title='Call Postback',
        payload='Payload for first bubble'
    )
    rift_element = elements.Element(
        title='rift',
        subtitle='Next-generation virtual reality',
        item_url='https://www.oculus.com/en-us/rift/',
        image_url='http://messengerdemo.parseapp.com/img/rift.png',
        buttons=[
            rift_web_button, rift_postback_button
        ]
    )

    touch_web_button = elements.WebUrlButton(
       title='Open Web URL',
       url='https://www.oculus.com/en-us/touch/'
    )
    touch_postback_button = elements.PostbackButton(
        title='Call Postback',
        payload='Payload for second bubble'
    )
    touch_element = elements.Element(
        title='touch',
        subtitle='Your Hands, Now in VR',
        item_url='https://www.oculus.com/en-us/touch/',
        image_url='http://messengerdemo.parseapp.com/img/touch.png',
        buttons=[
            rift_web_button, rift_postback_button
        ]
    )

    template = templates.GenericTemplate(       
       elements=[
           rift_element, touch_element
       ]
    )

    attachment = attachments.TemplateAttachment(template=template)
    message = messages.Message(attachment=attachment)
    request = messages.MessageRequest(recipient, message)

    messenger.send(request)

def send_text_message(recipient_id, message_text):
    message_data = json.dumps({
            "recipient": {
                "id": recipient_id
                },
            "message": {
                "text": "P: " + message_text #add P: before the text
            }
        })

    call_send_API(message_data)

def receive_postback(event):
    sender_id = event["sender"]["id"]
    recipient_id = event["recipient"]["id"]
    time_of_postback = event["timestamp"]
    time_converted = convert_timestame(time_of_postback)

    payload = event["postback"]["payload"]

    log("Received postback for user {sender} and page {recipient} with payload {payload} at {time}".format(
            sender=sender_id,
            recipient=recipient_id,
            payload=payload,
            time=time_of_postback
        ))

    send_text_message(sender_id, "Postback called")


if __name__ == '__main__':
    messenger_handler.register_event(EventHandler.EVENT_MESSAGE, receive_message)
    app.run(debug=True)    