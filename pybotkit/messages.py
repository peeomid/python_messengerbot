import json


class Message(object):

    def __init__(self, text=None, attachment=None, quick_replies=None, metadata=None):
        if not text and not attachment:
            raise ValueError('<Message> text or attachment must be set')
        self.text = text
        self.attachment = attachment
        self.quick_replies = quick_replies
        self._metadata = metadata
        # TODO check quick replies going with attachment
        # Quick Replies work with all message types including text message, 
        # image and template attachments. Please refer to the Send API documentation for more information on how to use the attachment object.
        # https://developers.facebook.com/docs/messenger-platform/send-api-reference/quick-replies


    @property
    def metadata(self):
        if len(self._metadata) > 1000:
            raise ValueError(
                'Message.metadata has more than 1000 characters'
            )
        return self._metadata

    def to_dict(self):
        data = {}
        if self.text:
            data['text'] = self.text
        if self.attachment:
            data['attachment'] = self.attachment.to_dict()
        if self.quick_replies:
            data['quick_replies'] = self.quick_replies.to_dict()
        if self.metadata:
            data['metadata'] = self.metadata
        return data


class Recipient(object):

    def __init__(self, recipient_id=None, phone_number=None):
        if not recipient_id and not phone_number:
            raise ValueError('<Recipient> id or phone_number must be set')
        self.recipient_id = recipient_id
        self.phone_number = phone_number

    def to_dict(self):
        if self.recipient_id:
            return {'id': self.recipient_id}
        return {'phone_number': self.phone_number}


class Request(object):

    NTIF_REGULAR = 'REGULAR'
    NTIF_SILENT = 'SILENT_PUSH'
    NTIF_NOPUSH = 'NO_PUSH'
    NOTIFICATION_TYPE_OPTIONS = (
        NTIF_REGULAR, NTIF_SILENT, NTIF_NOPUSH
    )

    def __init__(self, recipient, notification_type=None):
        self.recipient = recipient        
        self._notification_type = notification_type

    @property
    def notification_type(self):
        if self._notification_type:
            if self._notification_type not in self.NOTIFICATION_TYPE_OPTIONS:
                raise ValueError(
                    'notification_type valid options: %s' %
                    str(self.NOTIFICATION_TYPE_OPTIONS)
                )
        return self._notification_type

    def to_dict(self):
        data = {
            'recipient': self.recipient.to_dict()            
        }
        if self.notification_type:
            data['notification_type'] = self.notification_type
        return data

    def serialise(self):
        return json.dumps(self.to_dict())

class MessageRequest(Request):

    def __init__(self, recipient, message, notification_type=None):
        super(MessageRequest, self).__init__(recipient, notification_type)
        self.message = message

    def to_dict(self):
        data = super(MessageRequest, self).to_dict()
        data['message'] = self.message.to_dict()

        return data

class SenderActionRequest(Request):
    SO_MARK_SEEN = 'mark_seen'
    SO_TYPE_ON = 'typing_on'
    SO_TYPE_OFF = 'typing_off'
    SENDER_OPTIONS = (
        SO_MARK_SEEN, SO_TYPE_ON, SO_TYPE_OFF
    )

    def __init__(self, recipient, sender_action, notification_type=None):
        if sender_action not in self.SENDER_OPTIONS:
            raise ValueError(
                    'sender_option valid options: %s' %
                    str(self.SENDER_OPTIONS)
                )

        super(SenderAction, self).__init__(recipient, notification_type)
        self.sender_action = sender_action

    def to_dict(self):
        data = super(SenderAction, self).to_dict()
        data['sender_action'] = self.sender_action

        return data
