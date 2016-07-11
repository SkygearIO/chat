var $ = function(_id) {
  return document.getElementById(_id);
}

var inputVal = function(_id) {
  return $(_id).value;
}

var User = skygear.Record.extend('user');

class Demo {
  constructor(container, plugin) {
    this.container = container;
    this.plugin = plugin;
    this.endpointEl = $('endpoint');
    this.apiKeyEl = $('api-key');
    this.usernameEl = $('currentUsername');
    this.emailEl = $('currentEmail');
    this.tokenEl = $('accessToken');
    this.directConversationEl = $('direct-conversation');
    this.groupConversationEl = $('group-conversation');
  }

  restore() {
    var endPoint = localStorage.getItem('skygear-endpoint');
    if (endPoint === null) {
      endPoint = 'https://chat.skygeario.com/';
    }
    var apiKey = localStorage.getItem('skygear-apikey');
    if (apiKey === null) {
      apiKey = 'apikey';
    }
    this.configSkygear(endPoint, apiKey);
  }

  configSkygear(endPoint, apiKey) {
    this.container.config({
      endPoint: endPoint,
      apiKey: apiKey
    }).then(function () {
      localStorage.setItem('skygear-endpoint', skygear.endPoint);
      localStorage.setItem('skygear-apikey', skygear.apiKey);
      this.endpointEl.value = skygear.endPoint;
      this.apiKeyEl.value = skygear.apiKey;
      this.displayCurrentUser();
      this.plugin.subscribe(this._handler.bind(this));
    }.bind(this));
  }

  displayCurrentUser() {
    if (skygear.currentUser) {
      this.usernameEl.textContent = skygear.currentUser.username;
      this.emailEl.textContent = skygear.currentUser.email;
      this.tokenEl.textContent = this.container.accessToken;
    }
  }

  loginSkygear(username, pw) {
    return this.container.loginWithUsername(username, pw).then(function (result) {
      console.log(result);
      this.displayCurrentUser();
    }.bind(this));
  }

  signupSkygear(username, pw) {
    return this.container.signupWithUsername(username, pw).then(function (result) {
      console.log(result);
      this.displayCurrentUser();
    }.bind(this));
  }

  fetchUserTo(el) {
    var q = new skygear.Query(User);
    return this.container.publicDB.query(q).then(function (result) {
      var ul = $(el);
      ul.innerHTML = "";
      console.log(result);
      ul.textContent = JSON.stringify(result);
    });
  }

  fetchUnreadCountTo(conversationEl, messageEl) {
    return this.plugin.getUnreadCount().then(function (result) {
      var cEl = $(conversationEl);
      cEl.textContent = result.conversation;
      var mEl = $(messageEl);
      mEl.textContent = result.message;
    });
  }

  fetchConversationTo(conversationID, el) {
    return this.plugin.getConversation(conversationID).then(function (result) {
      var ul = $(el);
      console.log(result);
      ul.textContent = JSON.stringify(result);
    });
  }

  fetchConversationsTo(el) {
    return this.plugin.getConversations().then(function (result) {
      var ul = $(el);
      ul.innerHTML = "";
      console.log(result);
      ul.textContent = JSON.stringify(result);
    });
  }

  createDirectConversation(userID) {
    // FIXME: the SDK should strip the prefix for me.
    if (userID.startsWith("user/")) {
      userID = userID.substr(5);
    }
    return this.plugin.getOrCreateDirectConversation(userID).then(function (result) {
      console.log(result);
      this.directConversationEl.textContent = result._id;
    }.bind(this));
  }

  createConversation(user1, user2, user3) {
    let users = [];
    [user1, user2, user3].map(function (u) {
      if (u) {
        users.push(u);
      }
    });
    return this.plugin.createConversation(
        users,
        null,
        'From Demo'
      ).then(function (result) {
      console.log(result);
      this.groupConversationEl.textContent = result._id;
    }.bind(this));
  }

  addParticipant(conversationID, userID) {
    return this.plugin.addParticipants(conversationID, [userID]).then(function (result) {
      console.log(result);
    });
  }

  removeParticipant(conversationID, userID) {
    return this.plugin.removeParticipants(conversationID, [userID]).then(function (result) {
      console.log(result);
    });
  }

  markAsLastRead(conversationID, messageID, el) {
    return this.plugin.markAsLastMessageRead(conversationID, messageID).then(function (result) {
      var rEl = $(el);
      rEl.textContent = JSON.stringify(result);
    });
  }

  getMessagesTo(conversationID, limit, beforeTime, el) {
    return this.plugin.getMessages(conversationID, limit, beforeTime).then(function (result) {
      var ul = $(el);
      ul.innerHTML = "";
      console.log(result);
      ul.textContent = JSON.stringify(result);
    }.bind(this));
  }

  createMessage(conversationID, content, metadata, asset, el) {
    return this.plugin.createMessage(
      conversationID,
      content,
      metadata,
      asset
     ).then(function (result) {
      var ul = $(el);
      console.log(result);
      ul.textContent = JSON.stringify(result);
    }.bind(this));
  }

  _handler(data) {
    if (this.handler) {
      this.handler(data);
    } else {
      console.log(data);
    }
  }
}

