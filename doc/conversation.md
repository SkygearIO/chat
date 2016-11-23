# Conversation

In conversation, there will be admin and participants. Only admin can
add/remove everyone. While participants can only delete himself (leave
conversation).

If your app don't need two level of access control. Just use the participant
API. Removing user from participant will remove it from admins automatically.

If your app is public channel, you can set the ACL of the conversation object
to be public.

Related API:

- createConversation(participants, title, meta, options)
- createDirectConversation(participant, title, meta, options)
- deleteConversation(conversation)
- updateConversation(conversation)
- addParticipants(conversation, participants)
- removeParticipants(conversation, participants)
- addAdmins(conversation, admins)
- removeAdmins(conversation, admins)


## Creating a conversation

`createConversation(participants, title, meta, options)`

`meta` is a JSON attributes for app specific data.
`options` is have following options:
- distinctByParticipants (boolean, default to false)
- admins ([user], default to all participants)

Duplicate call of `createConversation` with same list of participants will
return the different conversation, unless `distinctByParticipants` in options is
set to `true`.

Adding or removing participants from a distinct conversation (see below) makes
it non-distinct.

All participant will be admin unless specific in `options.admins`

In common use case, one to one conversation is special. So we provided a
helper function for creating unique direct conversation.

`createDirectConversation(participant, title, meta)`

This helper function will create conversation with `distinctByParticipants`
set to `true`.

# Querying UserConversation

In common use case, application don't query the Conversation list only. They
query conversation list AND user specific data. Like `unread` count,
`last_read_message` for scroll position.

Related API:

- getUserConversations()
- getUserConversation(conversation)

Return a list of `UserConversation` object with transient include
`conversation` and `user`.

# Querying participants conversation last read

- getLastReadMessage(conversation)

Return a list of `user_id` to `message_id` mapping.

```
{
  'user/id1': 'message/uuid1',
  'user/id2': 'message/uuis2'
}
```
