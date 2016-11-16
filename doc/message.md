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
- markAsDelivery([messages])
- markAsLastMessageRead(conversation, message)
- getUnreadMessageCount(conversation)

# Receipt

Receipt is a Skygear Record point to User and Message, storing the message
delivery status. The status can be `delivered` and `read`.

Related API:
- getReceipt(message)

Q: Not sure we need `getReceipts([message])` (Never see a interface design
need it.)
