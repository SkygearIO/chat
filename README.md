# skygear-chat
Chat addon to provide common operation

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
