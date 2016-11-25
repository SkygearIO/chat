# Internal channel name

Each user will have a rotatable `_user_channel`. And all message are fanout at
the server side for security purpose.

The example record event payload are:

```
{
  "event": "update",
  "data": {
    'record_type': record_type,
    'event_type': event_type,
    'record': serialize_record(record),
    'original_record': serialize_orig_record
  }
}
```

The example typing event payload are:

```
{
  "event": "typing",
  "data": {
    "conversation/id1": {
      "user/id": {
        "event": "begin",
        "at": "20161116T78:44:00Z"
      },
      "user/id2": {
        "event": "begin",
        "at": "20161116T78:44:00Z"
      }
    }
  }
}
```

`event` can be `update`, `create`, `delete` and `typing`.


# Pubsub

- subscribe(callback)

This pass in callback will be invoked when messages to user participating
conversation is created/deleted. The fanout is done at server side.

format is as follow:

```
{
    'record_type': record_type,
    'event_type': event_type,
    'record': serialize_record(record),
    'original_record': serialize_orig_record
}
```

# TypingIndicator

- sendTypingIndicator(conversation, state)
- subscribeTypingIndicator(conversation, callback(payload))
- unsubscribeTypingIndicator(conversation)

Application developer should call `sendTypingIndicator`. With status `begin`,
`pause` and `finished`. The event are suggested to send in 1 second interval.
The events are ephemeral. And it is up to the application developer for how to
display the typing status. The callback will received payload as follow:

```
{
  'userid': {
    'event': 'begin',
    'at': '20161116T78:44:00Z'
  },
  'userid2': {
    'event': 'begin',
    'at': '20161116T78:44:00Z'
  }
}
```

Normally, you will not call `sendTypingIndicator` yourself, we provided helper
to bind to the input event that will send the event. You just subscribe the
indicator event in your application code.

# Message Receipt

This is PLANING. Not to implement in v2.

The pubsub channel is based on `user_id`

- subscribeReceipt(callback([Receipts])))

The behaviour is:

- When a receipts on a message is created/updated.
- plugin will collect all receipts on that message.
- send all receipts to the callback as array.
