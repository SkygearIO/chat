/* global skygear */
'use strict';

const uuid = require('uuid');
const _ = require('underscore');
const skygear = require('skygear');

const Conversation = skygear.Record.extend('conversation');
const ChatUser = skygear.Record.extend('chat_user');
const Message = skygear.Record.extend('message');
const UserChannel = skygear.Record.extend('user_channel');

module.exports = new function() {
  this.getChatUser = function() {
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
      }
      return record;
    });
  };

  this.createConversation = function(
                            participant_ids,
                            admin_ids,
                            title,
                            metadata) {
    const conversation = new Conversation();
    conversation.title = title;
    conversation.metadata = metadata;
    conversation.participant_ids = _.unique(participant_ids);
    conversation.admin_ids = _.unique(admin_ids);
    return skygear.publicDB.save(conversation);
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
    const _this = this;
    return _this.getConversation(conversation_id).then(function(conversation) {
      return skygear.publicDB.del(conversation);
    });
  };

  this.editConversation = function(conversation_id, changes) {
    const _this = this;
    return _this.getConversation(conversation_id).then(function(conversation) {
      if (changes.title !== undefined) {
        conversation.title = changes.title;
      }

      if (changes.metadata !== undefined) {
        conversation.metadata = changes.metadata;
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

  this.createMessage = function(conversation_id, body) {
    const message = new Message();
    message.conversation_id = conversation_id;
    message.body = body;
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

  this._getOrCreateUserChannel = function() {
    const query = new skygear.Query(UserChannel);
    const _this = this;
    return skygear.privateDB.query(query).then(function(records) {
      if (records.length > 0) {
        return records[0];
      }
      return null;
    }).then(function(record) {
      if (record === null) {
        const channel = new UserChannel();
        channel.name = uuid.v4()
        return skygear.privateDB.save(channel);
      }
      return record;
    });
  };

  this.subscribe = function(handler) {
    this._getOrCreateUserChannel().then(function(channel) {
      skygear.pubsub.connect();
      skygear.off(channel.name);
      skygear.on(channel.name, function(data) {
        data.record = JSON.parse(data.record);
        data.original_record = JSON.parse(data.original_record);
        handler(data);
      });
    });
  };

};
