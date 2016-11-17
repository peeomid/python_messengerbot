from future.utils import viewitems

import six
import re
from .utils import log


class EventHandler(object):
    """
    Event Handler
    event_handlers = {
        ''
    }
    compiled_patterns = {}
    pattern_handlers = {}
    attachment_handlers = {}
    quickreply_handlers = {}
    postback_handlers = {}

    """
    EVENT_MESSAGE = 'message'    
    EVENT_DELIVERY = 'message_delivered'
    EVENT_READ = 'message_read'
    EVENT_ECHO = 'message_echo'
    EVENT_QUICK_REPLY = 'message_quick_reply'  # when users click quick reply
    EVENT_ATTACHMENT = 'message_attachment'   # when users send an attachment
    EVENT_TEXT_MESSAGE = 'message_text'    # event on only text message is received

    EVENT_POSTBACK = 'facebook_postback'
    EVENT_OPTIN = 'facebook_optins'
    EVENT_REF = 'facebook_referral'
    EVENT_CHECKOUT_UPDATE = 'facebook_checkout_updates'
    EVENT_PAYMENT = 'facebook_payments'
    EVENT_ACCOUNT_LINKING = 'facebook_account_linking'

    EVENT_OPTIONS = [
        EVENT_MESSAGE,
        EVENT_DELIVERY,
        EVENT_READ,
        EVENT_ECHO,
        EVENT_QUICK_REPLY,
        EVENT_ATTACHMENT,
        EVENT_TEXT_MESSAGE,
        EVENT_POSTBACK,
        EVENT_OPTIN,
        EVENT_REF,
        EVENT_CHECKOUT_UPDATE,
        EVENT_PAYMENT,
        EVENT_ACCOUNT_LINKING,
    ]

    # attachments
    ATM_IMAGE = 'image'
    ATM_AUDIO = 'audio'
    ATM_VIDEO = 'video'
    ATM_FILE = 'file'
    ATM_LOCATION = 'location'
    ATM_OPTIONS = [
        ATM_IMAGE,
        ATM_AUDIO,
        ATM_VIDEO,
        ATM_FILE,
        ATM_LOCATION,
    ]

    def __init__(self):
        self.event_handlers = {}
        self.pattern_handlers = {}
        self.attachment_handlers = {}        
        self.quickreply_handlers = {}        
        self.compiled_patterns = {}
        self.postback_handlers = {}
    
    def webhook_handler(self, data):
        '''
        `data` from Facebook, in json format
        '''
        if data["object"] == "page":

            for entry in data["entry"]:
                page_id = entry["id"]
                time_of_event = entry["time"]

                for messaging_event in entry["messaging"]:

                    if messaging_event.get("optin"):    # optin confirmation
                        self._trigger_event(self.EVENT_OPTIN, messaging_event)                        

                    elif messaging_event.get("message"):  # someone sent us a message
                        self._trigger_event(self.EVENT_MESSAGE, messaging_event)
                        self._handle_message_content(messaging_event)
                        
                    elif messaging_event.get("delivery"):  # delivery confirmation
                        self._trigger_event(self.EVENT_DELIVERY, messaging_event)
                    
                    elif messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                        self._trigger_event(self.EVENT_POSTBACK, messaging_event)
                        self._handle_postback_content(messaging_event)

                    elif messaging_event.get("read"):
                        self._trigger_event(self.EVENT_READ, messaging_event)

                    elif messaging_event.get("account_linking"):
                        self._trigger_event(self.EVENT_ACCOUNT_LINKING, messaging_event)
                    else:
                        # TODO handle unknown event
                        log("Unknown event received: {event} ".format(event=messaging_event))


    def _add_event_callback(self, event, callback):
        event = event.lower()   #convert all lower case

        if event in self.EVENT_OPTIONS:            
            if event not in self.event_handlers:
                self.event_handlers[event] = []

            self.event_handlers[event].append(callback)
            log("added event, and handlers {handlers}".format(handlers=self.event_handlers))        
        else:
            raise ValueError(
                'Unknown event given'
            )


    def register_event(self, event, callback):
        '''
        To register a callback on given event
        '''
        self._add_event_callback(event, callback)


    def on_event(self, events):
        '''
        Decorator for registering function on event
        `events` can be passed as:
        - string: one single event
        - list of events: multiple events
        '''
        def decorator(func):
            local_events = events
            if isinstance(local_events, six.string_types):
                local_events = [local_events]
            for local_event in local_events:                
                self.register_event(local_event, func)
            return func        
        return decorator


    def _trigger_event(self, event, messaging_event):
        '''
        Trigger an event
        Go through all registerd callback and run them
        '''
        log("trigger event '{event}'".format(event=event))
        if event in self.EVENT_OPTIONS:
            log("event in")
            log("handlers {handlers}".format(handlers=self.event_handlers))
            if event in self.event_handlers:
                log("in event handlers")                
                for callback in self.event_handlers[event]:
                    callback(messaging_event)    

    def _add_payload_callback(self, type, payload, callback):
        '''
        Used for exact match of quick reply and postback
        type can be either `quickreply` or `postback`
        '''
        if type == 'quickreply':
            handlers = self.quickreply_handlers
        elif type == 'postback':
            handlers = self.postback_handlers
        else:
            return
        
        if payload not in handlers:
            handlers[payload] = []

        handlers[payload].append(callback)


    # def _register_payload():
    #     pass
    def _on_payload(self, type, payloads):
        '''
        decorator for registering exact match of payload (quick reply and postback)
        type can be either `quickreply` or `postback`
        '''
        def decorator(func):
            local_payloads = payloads
            if isinstance(local_payloads, six.string_types):
                local_payloads = [local_payloads]
            for local_payload in local_payloads:                
                self._add_payload_callback(type, local_payload, func)
            return func
        return decorator

    def _trigger_payload(self, type, payload, messaging_event):
        '''
        Trigger an event
        Go through all registerd callback and run them
        '''                
        if type == 'quickreply':
            handlers = self.quickreply_handlers
        elif type == 'postback':
            handlers = self.postback_handlers
        else:
            return

        if payload in handlers:            
            for callback in handlers[payload]:
                callback(messaging_event)

    def _add_quickreply_callback(self, payload, callback):
        self._add_payload_callback('quickreply', payload, callback)

    def register_quickreply(self, payload, callback):
        self._add_quickreply_callback(payload, callback)

    def on_quickreply(self, payloads):
        return self._on_payload('quickreply', payloads)

    def _trigger_quickreply(self, payload, messaging_event):
        self._trigger_payload('quickreply', payload, messaging_event)


    def _add_postback_callback(self, payload, callback):
        self._add_payload_callback('postback', payload, callback)

    def register_postback(self, payload, callback):
        self._add_postback_callback(payload, callback)

    def on_postback(self, payloads):
        return self._on_payload('postback', payloads)

    def _trigger_postback(self, payload, messaging_event):
        self._trigger_payload('postback', payload, messaging_event)



    def _add_pattern_callback(self, pattern, callback):
        if pattern not in self.compiled_patterns:
            self.compiled_patterns[pattern] = re.compile(pattern)
        if pattern not in self.pattern_handlers:
            self.pattern_handlers[pattern] = []

        self.pattern_handlers[pattern].append(callback)

    def register_pattern(self, pattern, callback):
        self._add_pattern_callback(pattern, callback)

    def hears(self, patterns):
        '''
        decorator for registering exact match of payload (quick reply and postback)
        type can be either `quickreply` or `postback`
        pattern should be in raw text
        '''        
        def decorator(func):
            local_patterns = patterns            
            if isinstance(local_patterns, six.string_types):
                local_patterns = [local_patterns]
            for local_pattern in local_patterns:                
                self.register_pattern(local_pattern, func)
            return func
        return decorator

    def _trigger_text_pattern_check(self, text, messaging_event):
        '''        
        Go through all registered pattern to check if given text matches any
        if matched, call registered callback
        '''        
        for (pattern, callbacks) in viewitems(self.pattern_handlers):
            if pattern not in self.compiled_patterns:
                self.compiled_patterns[pattern] = re.compile(pattern)

            regex = self.compiled_patterns[pattern]
            if regex.search(text):
                # If matches found, run through all callbacks
                for callback in callbacks:
                    callback(messaging_event)
            else:
                # Allow multiple matches?
                pass


    def _add_attachment_callback(self, attachment_type, callback):        
        if attachment_type not in self.attachment_handlers:
            self.attachment_handlers[attachment_type] = []

        self.attachment_handlers[attachment_type].append(callback)

    def register_attachment(self, attachment_type, callback):
        self._add_attachment_callback(attachment_type, callback)

    def on_attachment(self, attachment_types):
        '''
        decorator for registering attachment type        
        '''
        def decorator(func):
            local_types = attachment_types
            if isinstance(local_types, six.string_types):
                local_types = [local_types]
            for local_type in local_types:                
                self.register_attachment(local_type, func)
            return func
        return decorator

    def _trigger_attachment_type(self, attachment_type, attachment, messaging_event):
        if attachment_type in self.attachment_handlers:            
            for callback in self.attachment_handlers[attachment_type]:
                callback(attachment, messaging_event)


    def _handle_attachment_content(self, messaging_event):
        message = messaging_event.get("message")
        message_attachments = message.get("attachments")

        for attachment in message_attachments:            
            attachment_type = attachment.get("type")
            if attachment_type:
                self._trigger_attachment_type(attachment_type, attachment, messaging_event)




    def _handle_message_content(self, messaging_event):
        '''
        Go into message content to trigger events
        '''

        sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
        recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID    
        time_of_message = messaging_event["timestamp"]        
        message = messaging_event.get("message")

        log("Received message for user {sender_id} and page {recipient_id} at {time} with message:".format(sender_id=sender_id, recipient_id=recipient_id, time=time_of_message))
        # log(message)    

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

            self._trigger_event(self.EVENT_ECHO, messaging_event)
            return
        elif quick_reply:
            # quick_reply_payload = quick_reply["payload"]
            log("Quick reply for message {message_id} with payload {payload}".format(
                    message_id=message_id,
                    payload=quick_reply_payload
                ))            
            self._trigger_event(self.EVENT_QUICK_REPLY, messaging_event)            
            self._handle_quickreply_content(messaging_event)
            
            return

        # If we receive a text message, check to see if it matches a keyword
        # and send back the example. Otherwise, just echo the text we received.
        if message_text:
            self._trigger_event(self.EVENT_TEXT_MESSAGE, messaging_event)
            self._trigger_text_pattern_check(message_text, messaging_event)
        elif message_attachments:
            # send_text_message(sender_id, "Message with attachment received")        
            self._trigger_event(self.EVENT_ATTACHMENT, messaging_event)
            self._handle_attachment_content(messaging_event)

    def _handle_postback_content(self, messaging_event):
        # sender_id = event.get("sender").get("id")
        # recipient_id = event["recipient"]["id"]        

        payload = messaging_event.get("postback").get("payload")

        # log("Received postback for user {sender} and page {recipient} with payload {payload} at {time}".format(
        #         sender=sender_id,
        #         recipient=recipient_id,
        #         payload=payload,
        #         time=time_of_postback
        #     ))
        
        if payload:                    
            self._trigger_postback(payload, messaging_event)

    def _handle_quickreply_content(self, messaging_event):
        payload = messaging_event.get("message").get("quick_reply").get("payload")

        if payload:
            self._trigger_quickreply(payload, messaging_event)