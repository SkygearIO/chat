'use strict';

const skygear = require('skygear');
const _ = require('underscore');
skygear.endPoint = 'http://localhost:3001/';
skygear.configApiKey('my_skygear_key');

const Conversation = skygear.Record.extend('conversation');
const ChatUser = skygear.Record.extend('chat_user');
const Message = skygear.Record.extend('message');

const container = function() {};

container._skygear = skygear;

container.getChatUser = function() {
  const query = new this._skygear.Query(ChatUser);
  query.equalTo('_owner_id', this._skygear.currentUser.id);

  return this._skygear.publicDB.query(query).then(function(records) {
    if (records.length > 0) {
      return records[0];
    }
  }).then(function(record) {
    if (record === null) {
      const user = new ChatUser();
      return this._skygear.publicDB.save(user);
    }
    return record;
  });
};

container.createConversation = function(
                          participant_ids,
                          admin_ids,
                          is_direct_message,
                          distinct,
                          title,
                          metadata) {
  const conversation = new Conversation();
  conversation.is_direct_message = is_direct_message;
  conversation.title = title;
  conversation.metadata = metadata;
  conversation.participant_ids = _.unique(participant_ids);
  conversation.admin_ids = _.unique(admin_ids);
  return this._skygear.publicDB.save(conversation);
};

container.getConversation = function(conversation_id) {
  const query = this._skygear.Query(Conversation);
  query.equalTo('_id', conversation_id);
  return this._skygear.publicDB.query(query).then(function(records) {
    if (records.length > 0) {
      return records[0];
    }
    throw new Error('no conversation found');
  });
};

container.getConversations = function() {
  const query = this._skygear.Query(Conversation);
  query.containsValue('participant_ids', this._skygear.currentUser.id);
  return this._skygear.publicDB.query(query);
};

container.deleteConversation = function(conversation_id) {
  const _this = this;
  return _this.getConversation(conversation_id).then(function(conversation) {
    return _this._skygear.publicDB.del(conversation);
  });
};

container.editConversation = function(conversation_id, changes) {
  const _this = this;
  return _this.getConversation(conversation_id).then(function(conversation) {
    if (changes.title !== undefined) {
      conversation.title = changes.title;
    }

    if (changes.metadata !== undefined) {
      conversation.metadata = changes.metadata;
    }

    return _this._skygear.publicDB.save(conversation);
  });
};

container.addParticipants = function(conversation_id, participant_ids) {
  const _this = this;
  return _this.getConversation(conversation_id).then(function(conversation) {
    conversation.participant_ids = _.union(
        conversation.participant_ids, participant_ids);

    return _this._skygear.publicDB.save(conversation);
  });
};

container.removeParticipants = function(conversation_id, participant_ids) {
  const _this = this;
  return _this.getConversation(conversation_id).then(function(conversation) {
    conversation.participant_ids = _.difference(
        _.unique(conversation.participant_ids), participant_ids);

    return _this._skygear.publicDB.save(conversation);
  });
};

container.addAdmins = function(conversation_id, admin_ids) {
  const _this = this;
  return _this.getConversation(conversation_id).then(function(conversation) {
    conversation.admin_ids = _.union(
        conversation.admin_ids, admin_ids);

    return _this._skygear.publicDB.save(conversation);
  });
};

container.removeAdmins = function(conversation_id, admin_ids) {
  const _this = this;
  return _this.getConversation(conversation_id).then(function(conversation) {
    conversation.admin_ids = _.difference(
        _.unique(conversation.admin_ids), admin_ids);

    return _this._skygear.publicDB.save(conversation);
  });
};

container.createMessage = function(conversation_id, body) {
  const message = new Message();
  message.conversation_id = conversation_id;
  message.body = body;
  return this._skygear.privateDB.save(message);
};

module.exports = container;
