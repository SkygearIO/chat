# Message

Message is a normal Skygear Record represent individual messages. A message
must belong to a conversation.

Message have following attributes

- body (string)
- metadata (json)
- attachment (Skygear Asset)

Related API:

- createMessage(conversation, body, metadata, asset)
- getMessages(conversation, limit, before_time)

getMessage is a lambda that will return the Receipt info together if any.


# Read/Unread Message
- markAsRead([messages])
- markAsLastMessageRead(conversation, message)
- getUnreadMessageCount(conversation)

Internal method to be called automatically on SDK on client calling
`getMessages`. *Or we can do it at python side*
- `_markAsDelivery([messages])`

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
- getReceipt(message)

It will return an array of receipt object like following

```
[{
  'user_id': 'uuid',
  'read_at': '20161116T18:44:00Z'
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
