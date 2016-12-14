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

