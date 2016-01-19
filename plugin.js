'use strict';

const skygear = require('skygear');
skygear.endPoint = 'http://localhost:3001/';
skygear.configApiKey('my_skygear_key');

const Conversation = skygear.Record.extend('conversation');
const ChatUser = skygear.Record.extend('chat_user');

module.exports = {

  createChatUser: function() {
    const query = new skygear.Query(ChatUser);
    query.equalTo('_owner_id', skygear.currentUser.id);

    return skygear.publicDB.query(query).then(function(records) {
      if (records.length > 0) {
        return records[0];
      }

    }).then(function(record) {
        if (record === null) {
          const user = new ChatUser();
          return skygear.publicDB.save(user);
        } else {
          return record;
        }
    });
  },

  createConversation: function(
                          participant_ids, 
                          is_direct_message, 
                          distinct, 
                          title, 
                          metadata) {

    const query = new skygear.Query(ChatUser);
    query.contains('_owner_id', participant_ids);

    return skygear.publicDB.query(query).then(function(records) {
      if (records.length > 0) {
        return records;
      } else {
        throw new Error('no user found');
      }
    }).then(function(participants) {
      const conversation = new Conversation();
      conversation.is_direct_message = is_direct_message;
      conversation.title = title;
      conversation.metadata = metadata;

      conversation.participants = participants.map(function(participant) {
        return new skygear.Reference(participant);
      });

      return skygear.publicDB.save(conversation);
    });
  }

};
