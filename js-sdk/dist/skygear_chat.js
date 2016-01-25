/* global skygear */
'use strict';

const uuid = require('uuid');
const _ = require('underscore');

const Conversation = skygear.Record.extend('conversation');
const Message = skygear.Record.extend('message');
const UserChannel = skygear.Record.extend('user_channel');
const LastMessageRead = skygear.Record.extend('last_message_read');

module.exports = new function() {
  this.createConversation = function(
                            participant_ids,
                            admin_ids,
                            title) {
    const conversation = new Conversation();
    conversation.title = title;
    conversation.participant_ids = _.unique(participant_ids);
    conversation.admin_ids = _.unique(admin_ids);
    return skygear.publicDB.save(conversation);
  };

  this.getOrCreateDirectConversation = function(user_id) {
    const query = skygear.Query(Conversation);
    query.containsValue('participant_ids', skygear.currentUser.id);
    query.containsValue('participant_ids', user_id);
    query.equalTo('is_direct_message', true);
    query.limit = 1;
    return skygear.publicDB.query(query).then(function(records) {
      if (records.length > 0) {
        return records[0];
      }
      const conversation = new Conversation();
      conversation.participant_ids = [skygear.currentUser.id, user_id];
      conversation.admin_ids = [];
      conversation.is_direct_message = true;
      return skygear.publicDB.save(conversation);
    });
  };

  this.getConversation = function(conversation_id) {
    const query = skygear.Query(Conversation);
    query.equalTo('_id', conversation_id);
    return skygear.publicDB.query(query).then(function(records) {
      if (records.length > 0) {
        return records[0];
      }
      throw new Error('no conversation found');
    });
  };

  this.getConversations = function() {
    const query = skygear.Query(Conversation);
    query.containsValue('participant_ids', skygear.currentUser.id);
    return skygear.publicDB.query(query);
  };

  this.deleteConversation = function(conversation_id) {
    return this.getConversation(conversation_id).then(function(conversation) {
      return skygear.publicDB.del(conversation);
    });
  };

  this.updateConversation = function(conversation_id, changes) {
    const _this = this;
    return _this.getConversation(conversation_id).then(function(conversation) {
      if (changes.title !== undefined) {
        conversation.title = changes.title;
      }

      return skygear.publicDB.save(conversation);
    });
  };

  this.addParticipants = function(conversation_id, participant_ids) {
    const _this = this;
    return _this.getConversation(conversation_id).then(function(conversation) {
      conversation.participant_ids = _.union(
          conversation.participant_ids, participant_ids);

      return skygear.publicDB.save(conversation);
    });
  };

  this.removeParticipants = function(conversation_id, participant_ids) {
    const _this = this;
    return _this.getConversation(conversation_id).then(function(conversation) {
      conversation.participant_ids = _.difference(
          _.unique(conversation.participant_ids), participant_ids);

      return skygear.publicDB.save(conversation);
    });
  };

  this.addAdmins = function(conversation_id, admin_ids) {
    const _this = this;
    return _this.getConversation(conversation_id).then(function(conversation) {
      conversation.admin_ids = _.union(
          conversation.admin_ids, admin_ids);

      return skygear.publicDB.save(conversation);
    });
  };

  this.removeAdmins = function(conversation_id, admin_ids) {
    const _this = this;
    return _this.getConversation(conversation_id).then(function(conversation) {
      conversation.admin_ids = _.difference(
          _.unique(conversation.admin_ids), admin_ids);

      return skygear.publicDB.save(conversation);
    });
  };

  this.createMessage = function(conversation_id, body, metadata) {
    const message = new Message();
    message.conversation_id = conversation_id;
    message.body = body;

    if (metadata === undefined) {
      message.metadata = {};
    } else {
      message.metadata = metadata;
    }

    return skygear.privateDB.save(message);
  };

  this.getMessages = function(conversation_id, limit, before_time) {
    return skygear
      .lambda('chat:get_messages', [conversation_id, limit, before_time])
      .then(function(data) {
        for (var i = 0; i < data.results.length; i++) {
          data.results[i]._created_at = new Date(
            data.results[i]._created_at);
        }
        return data;
      });
  };

  this.markAsLastMessageRead = function(conversation_id, message_id) {
    return _getOrCreateLastMessageRead(conversation_id).then(
      function(record) {
        record.message_id = message_id;
        return skygear.privateDB.save(record);
      });
  };

  this.getUnreadMessageCount = function(conversation_id) {
    return skygear.lambda('chat:get_unread_message_count', [conversation_id])
      .then(function(data) {
        return data.count;
      });
  };

  this.subscribe = function(handler) {
    _getOrCreateUserChannel().then(function(channel) {
      skygear.pubsub.connect();
      skygear.off(channel.name);
      skygear.on(channel.name, function(data) {
        data.record = JSON.parse(data.record);
        data.original_record = JSON.parse(data.original_record);
        handler(data);
      });
    });
  };

  function _getOrCreateUserChannel() {
    const query = new skygear.Query(UserChannel);
    return skygear.privateDB.query(query).then(function(records) {
      if (records.length > 0) {
        return records[0];
      }
      return null;
    }).then(function(record) {
      if (record === null) {
        const channel = new UserChannel();
        channel.name = uuid.v4();
        return skygear.privateDB.save(channel);
      }
      return record;
    });
  }

  function _getOrCreateLastMessageRead(conversation_id) {
    const query = skygear.Query(LastMessageRead);
    query.equalTo('conversation_id', conversation_id);
    query.limit = 1;
    return skygear.privateDB.query(query).then(function(records) {
      if (records.length > 0) {
        return records[0];
      }
      const record = new LastMessageRead();
      record.conversation_id = conversation_id;
      return skygear.privateDB.save(record);
    });
  }
};
