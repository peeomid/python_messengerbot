import os
import requests
from .utils import log

from . import elements


class MessengerException(Exception):
    pass


class MessengerError(object):

    def __init__(self, *args, **kwargs):
        self.__dict__.update(**kwargs)

    def raise_exception(self):
        raise MessengerException(
            getattr(self, 'error_data', self.message)
        )

class MessengerClient(object):

    # GRAPH_API_URL = 'https://graph.facebook.com/v2.6/me'
    GRAPH_API_URL = 'https://graph.facebook.com/v2.6'

    def __init__(self, access_token):
        self.access_token = access_token

    def send_API_request(self, endpoint, message):
        params = {
            'access_token': self.access_token
        }
        response = requests.post(
            '%s/me/%s' % (self.GRAPH_API_URL, endpoint),
            params=params,
            json=message
        )
        log("API request response: {response}".format(response=response.json()))
        if response.status_code != 200:
            MessengerError(
                **response.json()['error']
            ).raise_exception()
        return response.json()

    def get_API_info(self, endpoint, params=None):
        if params:
            request_params = params
        else:
            request_params = {}
        request_params['access_token'] = self.access_token
        
        response = requests.get(
            '%s/%s' % (self.GRAPH_API_URL, endpoint),
            params=request_params            
        )
        log("API request response: {response}".format(response=response.json()))
        if response.status_code != 200:
            MessengerError(
                **response.json()['error']
            ).raise_exception()
        return response.json()
        

    def send_messenger_API_request(self, endpoint, message):
        messenger_endpoint = "me/" + endpoint
        self.send_API_request(endpoint, message)

    def send(self, message):
        return self.send_messenger_API_request('messages', message=message.to_dict())        

    def add_greeting_text(self, text):
        # You can personalize the greeting text using the person's name. You can use the following template strings:
        # {{user_first_name}}
        # {{user_last_name}}
        # {{user_full_name}}
        # https://developers.facebook.com/docs/messenger-platform/thread-settings/greeting-text

        if len(text) > 160:
            raise ValueError('Greeting text limit is 160 characters')
        message = {
            'setting_type': 'greeting',
            'greeting':{
                'text': text
              }
        }

        return self.send_messenger_API_request('thread_settings', message=message)

    def remove_greeting_text(self):
        message = {
            'setting_type': 'greeting'
        }        

        return self.send_messenger_API_request('thread_settings', message=message)

    def add_getstarted_button(self, payload):
        message = {
            'setting_type': 'call_to_actions',
            'thread_state': 'new_thread',
            'call_to_actions':[
                {
                  'payload': payload
                }
            ]
        }

        return self.send_messenger_API_request('thread_settings', message=message)

    def remove_getstarted_button(self):
        message = {
            'setting_type': 'call_to_actions',
            'thread_state': 'new_thread'
        }
        return self.send_messenger_API_request('thread_settings', message=message)

    def set_example_persistent_menu(self):
        postback_button1 = elements.PostbackButton(
           title='Help',
           payload='DEVELOPER_DEFINED_PAYLOAD_FOR_HELP'
        )
        postback_button2 = elements.PostbackButton(
            title='Start a New Order',
            payload='DEVELOPER_DEFINED_PAYLOAD_FOR_START_ORDER'
        )
        web_button = elements.WebUrlButton(
           title='View Website',
           url='http://petersapparel.parseapp.com/'
        )

        actions = [
            postback_button1, postback_button2, web_button
        ]
        self.set_persistent_menu(actions)
        

    def set_persistent_menu(self, actions):        
        message = {
            'setting_type' : 'call_to_actions',
            'thread_state' : 'existing_thread',            
        }

        message['call_to_actions'] = [
            action.to_dict() for action in actions
        ]        
        return self.send_messenger_API_request('thread_settings', message=message)        

    def get_userprofile(self, userid):
        params = {
            'fields': 'first_name,last_name,profile_pic,locale,timezone,gender,is_payment_enabled'
        }

        self.get_API_info(userid, params=params)


    def subscribe_app(self):
        """
        Subscribe an app to get updates for a page.
        """
        response = requests.post(
            '%s/subscribed_apps' % self.GRAPH_API_URL,
            params={
                'access_token': self.access_token
            }
        )
        return response.status_code == 200


ENV_KEY = 'MESSENGER_PLATFORM_ACCESS_TOKEN'

if ENV_KEY in os.environ:
    messenger = MessengerClient(
        access_token=os.environ[ENV_KEY]
    )
