# Message

Message is a normal Skygear Record represent individual messages. A message
must belong to a conversation.

Message have following attributes

- body (string)
- metadata (json)
- attachment (Skygear Asset)

Related API:

- createMessage(conversation, body, metadata, asset)
  - Use `record:save`.

- getMessages(conversation, limit, before_time)
  - Use `chat:get_messages` lambda.
  - Will return the Receipt info together if any.


# Read/Unread Message
- markAsRead([message_id])
  - Use `chat:mark_as_read` lambda.
  - The lambda should be called with a list of message IDs for the message
    displayed to the user.
  - Do not need to call this lambda if privacy settings do not allow.
- markAsDelivered([message_id])
  - Use `chat:mark_as_delivered` lambda.
  - The lambda should be called with a list of message IDs upon getting
    the messages.
- markAsLastMessageRead(conversation, message)
  - Use `record:save` on `user_conversation` record_type.
- getUnreadMessageCount(conversation)
  - Use `record:fetch` on `user_conversation` record_type.

`message.conversationStatus`. This attributes is updated by the python plugin.
Having following possible value:

- `delivering` - status that the message is still not read the server(i.e.
  this value is SDK only. server will always start with `delivered`)
- `delivered` - server got the message but no read receipt
- `some_read` - server got one of the read receipt from user
- `all_read` - server got all read receipt from all user

When this `conversationStatus` is updated. You will get a message update
notification if you did `subscribe` to your channel. (See pubsub.md)

# Receipt

Receipt is a Skygear Record point to User and Message, storing the message
delivery status. The status can be `delivered` and `read`.

Related API:

- getReceipt(message_id)
  - Use `chat:get_receipt` lambda.

It will return an array of receipt object like following

```
[{
  "user_id": "uuid",
  "read_at": "20161116T18:44:00Z"
  "delivered__at": "20161116T18:44:00Z"
},
{
  ...
}]
```

Q: Not sure we need `getReceipts([message])` (Never see a interface design
need it.)

This API is intended for querying individual message receipts. If you are
looking for display individual user read til which message. Please check out
`UserConversation` section.
