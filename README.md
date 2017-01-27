[![Build Status](https://travis-ci.org/SkygearIO/chat.svg)](https://travis-ci.org/SkygearIO/chat)
# Chat Plugin for Skygear

## Related SDK

You can find the SDK code in following repos on github. You can also directly
install at the package manager.

- JS - [chat-SDK-JS](https://www.npmjs.com/package/skygear-chat) on npm

    Source: https://github.com/SkygearIO/chat-SDK-JS
- iOS - [SKYKitChat](https://cocoapods.org/pods/SKYKitChat) on cocoapods

    Source: https://github.com/SkygearIO/chat-SDK-iOS
- Android - [chat-SDK-Android] io.skygear.chat on jscentre

    Source: https://github.com/SkygearIO/chat-SDK-Android

### Get the demo running at Skygear cloud

__First__

Assumed you go registered at `https://portal.skygeario.com`

__Second__

git submodule to import the source code.

```
git submodule add https://github.com/SkygearIO/chat.git chat
```

In your cloud code, import the chat plugin. Skygear will load and lambda and
database hook will be ready for use.
```python

from skygear.settings import settings

from .chat import includeme

includeme(settings)
```

__Third__

Tell Skygear cloud to serve the asset from chat-SDK-JS demo folder

git submodule to import the JS SDK source code.

```
git submodule add https://github.com/SkygearIO/chat-SDK-JS.git chat-SDK-JS
```

```python
from skygear import static_assets
from skygear.utils.assets import relative_assets

@static_assets(prefix='demo')
def chat_demo():
    return relative_assets('chat-SDK-JS/demo')
```

`https://<your_app_name>.skygeario.com/static/demo/index.html`

### Sending push notification

Push notification can be implemented by the following code.
Please ensure APNS certificate and private key are properly setup,
if you are using [Skygear.io], you can configure it at the setting panel.

```python
from skygear.container import SkygearContainer
from skygear.options import options as skyoptions
from skygear.action import push_user

# Import the chat plugin module.
# If you not using pip for the plugin, you will have modify the following lines
# to use relative import.
# For example if you have the `chat` folder located at the root of the project,
# you should use `from .chat import ...` instead of `from chat import ...`
from chat.user_conversation import total_unread
from chat.conversation import Conversation

# Create a container so we can talk to skygear server
container = SkygearContainer(api_key=skyoptions.masterkey)

# Register a handler after message is saved
@skygear.after_save("message")
def push_message_after_save_handler(record, original_record, conn):
    message = Message.from_record(record)
    conversation = Conversation(message.fetchConversationRecord())

    # Fetch the owner of the message
    resp = container.send_action('record:query', {
            'record_type': 'user',
            'predicate': [
                'eq',
                {'$type': 'keypath', '$val': '_id'},
                record._owner_id
            ]
        })
    user_record = resp['result'][0]

    # Construct the message for push notification
    if conversation['title'] is None:
        push_message = '{0}: {1}'.format(user_record['name'], record['body'])
    else:
        push_message = '{0}@{1}: {2}'.format(user_record['name'], conversation['title'], record['body'])

    # Send push notification to each participant
    for participant_id in conversation.participant_set:
        # Except the message author
        if record._owner_id == participant_id:
            continue

        # Get the total unread message count
        total_unread_count = total_unread(participant_id)['message']

        # Finally send the notification
        push_user(
            container,
            participant_id,
            {
                'apns': {
                    'aps': {
                        'alert': push_message,
                    },
                    'badge': total_unread_count,
                },
            }
        )
```

### Understanding the model

In this chat plugin, we have various model. Its responsibility as follow.

- Conversation - storing information on who is the admins, conversation title,
  last message arrival time, etc.
- Message - actual message to be display on screen, including the related
  asset and metadata.
- UserConversation - the exist of this relation represent a user is participant
  of a conversation. It store information on user specific information to a
  conversation, like last read time and unread count.
- UserChatStatus - Storing data like `last_online`.
- Receipt - Storing the user receipt on message.

For API detail, please visit the platform specific API filie:

- [JS SDK](https://doc.esdoc.org/github.com/skygeario/chat-SDK-JS/)
- [iOS SDK](http://cocoadocs.org/docsets/SKYKitChat/)
- [Android SDK](https://docs.skygear.io/android/plugins/chat/reference/)
- [Skygear.io](https://skygear.io)

