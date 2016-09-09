/* global skygear */
const uuid = require('uuid');
const _ = require('underscore');

const Conversation = skygear.Record.extend('conversation');
const UserConversation = skygear.Record.extend('user_conversation');
const Message = skygear.Record.extend('message');
const UserChannel = skygear.Record.extend('user_channel');

function SkygearChatContainer() {
  this.createConversation = function(
                            participant_ids,
                            admin_ids,
                            title) {
    const conversation = new Conversation();
    conversation.title = title;
    conversation.participant_ids = _.unique(participant_ids);
    if (_.isEmpty(admin_ids)) {
      conversation.admin_ids = conversation.participant_ids;
    } else {
      conversation.admin_ids = _.unique(admin_ids);
    }
    return skygear.publicDB.save(conversation);
  };

  this.getOrCreateDirectConversation = function(user_id) {
    const query = new skygear.Query(Conversation);
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
      conversation.admin_ids = conversation.participant_ids;
      conversation.is_direct_message = true;
      return skygear.publicDB.save(conversation);
    });
  };

  this.getConversation = function(conversation_id) {
    const query = new skygear.Query(UserConversation);
    query.equalTo('user', skygear.currentUser.id);
    query.equalTo('conversation', conversation_id);
    query.transientInclude('user');
    query.transientInclude('conversation');
    return skygear.publicDB.query(query).then(function(records) {
      if (records.length > 0) {
        return records[0];
      }
      throw new Error('no conversation found');
    });
  };

  this.getConversations = function() {
    const query = new skygear.Query(UserConversation);
    query.equalTo('user', skygear.currentUser.id);
    query.transientInclude('user');
    query.transientInclude('conversation');
    return skygear.publicDB.query(query);
  };

  this.deleteConversation = function(conversation_id) {
    return this.getConversation(conversation_id)
      .then(function(userConversation) {
        const conversation = userConversation.$transient.conversation;
        return skygear.publicDB.del(conversation);
      });
  };

  this.updateConversation = function(conversation_id, changes) {
    return this.getConversation(conversation_id)
      .then(function(userConversation) {
        const conversation = userConversation.$transient.conversation;
        if (changes.title !== undefined) {
          conversation.title = changes.title;
        }

        return skygear.publicDB.save(conversation);
      });
  };

  this.addParticipants = function(conversation_id, participant_ids) {
    return this.getConversation(conversation_id)
      .then(function(userConversation) {
        const conversation = userConversation.$transient.conversation;
        conversation.participant_ids = _.union(
            conversation.participant_ids, participant_ids);

        return skygear.publicDB.save(conversation);
      });
  };

  this.removeParticipants = function(conversation_id, participant_ids) {
    return this.getConversation(conversation_id)
      .then(function(userConversation) {
        const conversation = userConversation.$transient.conversation;
        conversation.participant_ids = _.difference(
            _.unique(conversation.participant_ids), participant_ids);
        conversation.admin_ids = _.difference(
            _.unique(conversation.admin_ids), participant_ids);

        return skygear.publicDB.save(conversation);
      });
  };

  this.addAdmins = function(conversation_id, admin_ids) {
    return this.getConversation(conversation_id)
      .then(function(userConversation) {
        const conversation = userConversation.$transient.conversation;
        conversation.admin_ids = _.union(
            conversation.admin_ids, admin_ids);

        return skygear.publicDB.save(conversation);
      });
  };

  this.removeAdmins = function(conversation_id, admin_ids) {
    return this.getConversation(conversation_id)
      .then(function(userConversation) {
        const conversation = userConversation.$transient.conversation;
        conversation.admin_ids = _.difference(
            _.unique(conversation.admin_ids), admin_ids);

        return skygear.publicDB.save(conversation);
      });
  };

  this.createMessage = function(conversation_id, body, metadata, asset) {
    const message = new Message();
    message.conversation_id = new skygear.Reference(
      'conversation/' + conversation_id
    );
    message.body = body;

    if (metadata === undefined || metadata === null) {
      message.metadata = {};
    } else {
      message.metadata = metadata;
    }
    if (asset) {
      const skyAsset = new skygear.Asset({
        file: asset,
        name: asset.name
      });
      message.attachment = skyAsset;
    }

    return skygear.privateDB.save(message);
  };

  this.getUnreadCount = function() {
    return skygear
      .lambda('chat:total_unread');
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
    return _getUserConversation(conversation_id).then(function(uc) {
      uc.last_read_message = new skygear.Reference('message/' + message_id);
      return skygear.publicDB.save(uc);
    });
  };

  this.getUnreadMessageCount = function(conversation_id) {
    return _getUserConversation(conversation_id).then(function(uc) {
      return uc.unread_count;
    });
  };

  this.subscribe = function(handler) {
    _getOrCreateUserChannel().then(function(channel) {
      skygear.pubsub.connect();
      skygear.off(channel.name);
      skygear.on(channel.name, function(data) {
        data.record = data.record;
        data.original_record = data.original_record;
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

  function _getUserConversation(conversation_id) {
    const ucQuery = new skygear.Query(UserConversation);
    ucQuery.equalTo('user', skygear.currentUser.id);
    ucQuery.equalTo('conversation', conversation_id);
    ucQuery.limit = 1;
    return skygear.publicDB.query(ucQuery).then(function(records) {
      if (records.length > 0) {
        return records[0];
      }
      throw new Error('No UserConversation found');
    });
  }
}

module.exports = new SkygearChatContainer();
