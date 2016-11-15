
class Attachment(object):

    def to_dict(self):
        return {
            'type': self.attachment_type,
            'payload': self.payload
        }

class LinkAttachment(Attachment):

    def __init__(self, url):
        self._url = url

    @property
    def payload(self):
        return {
            'url': self._url
        }


class ImageAttachment(LinkAttachment):
    attachment_type = 'image'
    

class AudioAttachment(LinkAttachment):
    attachment_type = 'audio'

class VideoAttachment(LinkAttachment):
    attachment_type = 'video'

class FileAttachment(LinkAttachment):
    attachment_type = 'file'    
    

class TemplateAttachment(Attachment):

    attachment_type = 'template'

    def __init__(self, template):
        self.template = template

    @property
    def payload(self):
        return self.template.to_dict()
