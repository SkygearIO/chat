# Skygear-chat
Chat addon to provide common operation

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

from .chat import plugin as chat_plugin


@static_assets(prefix='demo')
def chat_demo():
    return relative_assets('chat/js-sdk/demo')
```

`https://<your_app_name>.skygeario.com/static/demo/index.html`


# APIs

## createConversation(participant_ids, admin_ids, title)
create a conversation

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| participant_ids  | <code>Array</code> | |
| admin_ids | <code>Array</code> | |
| title | <code>String</code> | |


## getConversation(conversation_id)
retrieve a conversation by id

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |


## getConversations()
get all conversations in which the current user is participating


## updateConversation(conversation_id, changes)
edit a conversation (only admin)

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |
| changes | <code>Object</code> | |

available parameters of changes:

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| title | <code>String</code> | |


## deleteConversation(conversation_id)
delete a conversation by id (only admin)

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |


## deleteConversation(conversation_id)
delete a conversation by id (only admin)

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |

## getOrCreateDirectConversation(user_id)
get the existing direct conversation, or create if not exists

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| user_id  | <code>String</code> | |

## addParticipants(conversation_id, participant_ids)
add participants to a conversation (only admin)

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |
| participant_ids  | <code>Array</code> | |


## removeParticipants(conversation_id, participant_ids)
remove participants from a conversation (only admin)

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |
| participant_ids  | <code>Array</code> | |


## addAdmins(conversation_id, admin_ids)
add admins to a conversation (only admin)

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |
| participant_ids  | <code>Array</code> | |


## removeAdmins(conversation_id, admin_ids)
remove admins from a conversation (only admin)

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |
| participant_ids  | <code>Array</code> | |


## createMessage(conversation_id, body, metadata)
send a message to a conversation (only participants)

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |
| body| <code>String</code> | |
| metadata| <code>Object</code> | |


## getMessages(conversation_id, limit, before_time)
get messages from a conversation in descending order of created_at

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |
| limit | <code>Number</code> | integer |
| before_time | <code>Date</code> | optional |


## getUnreadMessageCount(conversation_id)
get unread message count of a conversation of the current user 

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |


## markAsLastMessageRead(conversation_id, message_id)
update last message read of the current user, 
required by getUnreadMessageCount 

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| conversation_id  | <code>String</code> | |
| message_id | <code>String</code> | |


## subscribe(handler)
set the subscriber for events received

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| handler| <code>function</code> |  |

the handler should accept data with the following structure:

| Param  | Type                | Description  |
| ------ | ------------------- | ------------ |
| record_type | <code>String</code> | conversation or message |
| event_type | <code>String</code> | create, update or delete |
| record | <code>Object</code> |  |
| original_record | <code>Object</code> |  |
