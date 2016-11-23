[![Build Status](https://travis-ci.org/SkygearIO/chat.svg)](https://travis-ci.org/SkygearIO/chat)
# Chat Plugin for Skygear

## Related SDK

You can find the SDK code in following repos on github. You can also directly
install at the package manager. 

JS - chat-SDK-JS (skygear-chat at npm)
iOS - chat-SDK-iOS (SKYKit/Chat on cocoapods)
Android - chat-SDK-Android (io.skygear.chat on jscentre)

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
from .chat import plugin as chat_plugin
```

__Third__

Tell Skygear cloud to serve the asset from demo folder

```python
from skygear import static_assets
from skygear.utils.assets import relative_assets

from .chat import *


@static_assets(prefix='demo')
def chat_demo():
    return relative_assets('chat/js-sdk/demo')
```

`https://<your_app_name>.skygeario.com/static/demo/index.html`

__Fourth__

Update database schema

`curl https://<your_app_name>.skygeario.com/chat-plugin-init`


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

- [JS SDK](./JSAPI.md)
- [iOS SDK] - WIP
- [Android SDK] - WIP

