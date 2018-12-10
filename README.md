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

### Quick Start

We provide Quick Start tutorial in different language.

- [Javascript][js-quick-start]
- [Android][android-quick-start]
- [iOS][ios-quick-start]

We also have basic guide go through feature by feature.

- [Javascript][js-basic]
- [Android][android-basic]
- [iOS][ios-basic]

### Understanding the model

In this chat plugin, we have various model represent different data in
application. Understanding the model relation make you able to use the plugin
efficiently. It also enable developer to store application specific data in
the correct model.

Following is the model relation diagram.

![Entity Relation][er]

#### Overview of models responsibility are as follow.

- Conversation - represent a conversation, it store conversation information
  like title, last message, no. of participant.
- Message - actual message display on screen, it store message text,
  related asset and metadata.
- UserConversation - represent a user is participating a conversation. It
  stores user specific information to a conversation, like last
  read time and unread count.
- Receipt - Store the user receipt on a message.

### Details attributes on models

Following is the table of attributes ensured by this plugin.

Note that `User` is Skygear provided User profile model.

__User__

| Attributes  | Type                | Description  |
| ------ | ------------------- | ------------ |
| name  | <code>String</code> | |

__Conversation__

| Attributes  | Type                | Description  |
| ------ | ------------------- | ------------ |
| title  | <code>String</code> | |
| admin_ids | <code>JSON Array</code> | |
| participant_ids | <code>JSON Array</code> | |
| participant_count | <code>Number</code> | |
| distinct_by_participants | <code>Boolean</code> | |
| metadata | <code>JSON Object</code> | |
| last_message | <code>Reference</code> | |

__Message__

| Attributes  | Type                | Description  |
| ------ | ------------------- | ------------ |
| body  | <code>String</code> | |
| conversation_status | <code>String</code> | Summary of receipt status |
| attachment | <code>Asset</code> | |
| metadata | <code>JSON Object</code> | |
| conversation_id | <code>Reference</code> | |

__UserConversation__

| Attributes  | Type                | Description  |
| ------ | ------------------- | ------------ |
| unread_count  | <code>Number</code> | |
| last_read_message | <code>Reference</code> | |
| user | <code>Reference</code> | |
| conversation | <code>Reference</code> | |

__Receipt__

| Attributes  | Type                | Description  |
| ------ | ------------------- | ------------ |
| read_at  | <code>Datetime</code> | |
| delivered_at | <code>Datetime</code> | |
| user_id | <code>Reference</code> | |
| message_id | <code>Reference</code> | |

## Detail API

For API detail, please visit the platform specific API filie:

- [JS SDK](https://docs.skygear.io/js/chat/reference/latest/)
- [iOS SDK](https://docs.skygear.io/ios/chat/reference/latest/)
- [Android SDK](https://docs.skygear.io/android/chat/reference/latest/)
- [Skygear.io](https://skygear.io)

[er]: https://github.com/SkygearIO/chat/raw/master/doc/er.png "ER diagram"
[js-quick-start]: https://docs.skygear.io/guides/chat/quick-start/js/
[android-quick-start]: https://docs.skygear.io/guides/chat/quick-start/android/
[ios-quick-start]: https://docs.skygear.io/guides/chat/quick-start/ios/
[js-basic]: https://docs.skygear.io/guides/chat/basics/js/
[android-basic]: https://docs.skygear.io/guides/chat/basics/android/
[ios-basic]: https://docs.skygear.io/guides/chat/basics/ios/

## Some sample code

### Sending push notification

Push notification can be implemented by the following code.
Please ensure APNS certificate and private key are properly setup,
if you are using [Skygear.io], you can configure it at the setting panel.

```python
import skygear
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
from chat.message import Message

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
                        'sound': 'default',
                        'badge': total_unread_count,
                    },
                    'from': 'skygear-chat',
                    'operation': 'notification'
                },
            }
        )
```

## Support
For implementation related questions or technical support, please find us on the [official forum](https://discuss.skygear.io) or [community chat](https://slack.skygear.io); For bug reports or feature requests, feel free to open an issue in this repo
