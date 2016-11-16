# Conversation

In conversation, there will be admin and participants. Only admin can
add/remove everyone. While participants can only delete himself (leave
conversation).

If your app don't need two level of access control. Just use the participant
API. Removing user from participant will remove it from admins automatically.

Related API:

- createConversation(participants, title, options)
- deleteConversation(conversation)
- updateConversation(conversation)
- addParticipants(conversation, participants)
- removeParticipants(conversation, participants)
- addAdmins(conversation, admins)
- removeAdmins(conversation, admins)


## Creating a conversation

`createConversation(participants, title, options)`

available options:
- distinctByParticipants (boolean, default to true)
- admins ([user], default to all participants)

Duplicate call of `createConversation` with same list of participants will
return the same conversation, unless `distinctByParticipants` in options is set
to `false`. When `distinctByParticipants` is set to `false`, every call to 
`createConversation` will create a new conversation.

Adding or removing participants from a distinct conversation (see below) makes
it non-distinct.

All participant will be admin unless specific in `options.admins`

# Querying UserConversation

In common use case, application don't query the Conversation list only. They
query conversation list AND user specific data. Like `unread` count,
`last_read_message` for scroll position.

Related API:

- getUserConversations()
- getUserConversation(conversation)

Return a list of `UserConversation` object with transient include
`conversation` and `user`.

