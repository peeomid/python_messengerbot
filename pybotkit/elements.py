

class Element(object):

    def __init__(self, title, item_url=None,
                 image_url=None, subtitle=None, buttons=None):

        self._title = title
        self.item_url = item_url
        self.image_url = image_url
        self._subtitle = subtitle
        self.buttons = buttons

    @property
    def title(self):
        if len(self._title) > 45:
            raise ValueError(
                'Element.title has more than 45 characters'
            )
        return self._title

    @property
    def subtitle(self):
        if self._subtitle:
            if len(self._subtitle) > 80:
                raise ValueError(
                                 'Element.subtitle has more than 80 characters'
                                 )
        return self._subtitle

    def to_dict(self):
        serialised = {
            'title': self.title,
            'item_url': self.item_url,
            'image_url': self.image_url,
            'subtitle': self.subtitle
        }
        if self.buttons:
            serialised['buttons'] = [
                button.to_dict() for button in self.buttons
            ]
        return serialised

class Button(object):

    def __init__(self, title):
        if len(title) > 20:
            raise ValueError('Button title limit is 20 characters')
        self.title = title

    def to_dict(self):
        serialised = {
            'type': self.button_type,
            'title': self.title
        }
        
        return serialised

class ShareButton(object):
    # The Share Button only works with the Generic Template
    # How to check this?
    
    def to_dict(self):
        serialised = {
            'type': 'element_share',            
        }
        
        return serialised

class WebUrlButton(Button):
    HR_COMPACT = 'compact'
    HR_TALL = 'tall'
    HR_FULL = 'full'
    HEIGHT_RATIO_OPTIONS = (
        HR_COMPACT, HR_TALL, HR_FULL
    )

    button_type = 'web_url'

    def __init__(self, title, url, height_ratio=None):
        self.url = url
        super(WebUrlButton, self).__init__(title=title)
        self.webview_height_ratio = height_ratio

    def to_dict(self):
        serialised = super(WebUrlButton, self).to_dict()
        serialised['url'] = self.url
        serialised['webview_height_ratio'] = self.webview_height_ratio        

        return serialised


class PostbackButton(Button):

    button_type = 'postback'

    def __init__(self, title, payload):
        self.payload = payload
        super(PostbackButton, self).__init__(title=title)

    def to_dict(self):
        serialised = super(PostbackButton, self).to_dict()
        serialised['payload'] = self.payload

        return serialised

class PhoneNumberButton(Button):

    button_type = 'phone_number'

    def __init__(self, title, payload):
        self.payload = payload
        super(PhoneNumberButton, self).__init__(title=title)

    def to_dict(self):
        serialised = super(PhoneNumberButton, self).to_dict()
        serialised['payload'] = self.payload

        return serialised


class QuickReply(object):    

    def to_dict(self):
        serialised = {
            'content_type': self.content_type,            
        }
        
        return serialised

class TextQuickReply(QuickReply):

    content_type = 'text'

    def __init__(self, title, payload, image_url=None):
        if len(title) > 20:
            raise ValueError('Button title limit is 20 characters')
        self.title = title
        self.payload = payload
        self.image_url = image_url

    def to_dict(self):
        serialised = super(TextQuickReply, self).to_dict()

        serialised['title'] = self.title
        serialised['payload'] = self.payload        
        if self.image_url:
            serialised['image_url'] = self.image_url

        return serialised


class LocationQuickReply(QuickReply):

    content_type = 'location'
