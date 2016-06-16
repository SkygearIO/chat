var $ = function(_id) {
  return document.getElementById(_id);
}

var inputVal = function(_id) {
  return $(_id).value;
}

const User = skygear.Record.extend('user');

class Demo {
  constructor(container, plugin) {
    this.container = container;
    this.plugin = plugin;
    this.usernameEl = $('currentUsername');
    this.emailEl = $('currentEmail');
    this.tokenEl = $('accessToken');
  }

  configSkygear(endPoint, apiKey) {
    this.container.config({
      endPoint: endPoint,
      apiKey: apiKey
    }).then(function () {
      this.displayCurrentUser();
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
    const q = new skygear.Query(User);
    return this.container.publicDB.query(q).then(function (result) {
      const ul = $(el);
      ul.innerHTML = "";
      console.log(result);
      ul.textContent = JSON.stringify(result);
    });
  }

  fetchConversationTo(el) {
    return this.plugin.getConversations().then(function (result) {
      const ul = $(el);
      ul.innerHTML = "";
      console.log(result);
      ul.textContent = JSON.stringify(result);
    });
  }

  createDirectConversation(userID) {
    return this.plugin.getOrCreateDirectConversation(userID).then(function (result) {
      console.log(result);
    });
  }

  getMessagesTo(conversationID, limit, beforeTime, el) {
    return this.plugin.getMessages(conversationID, limit, beforeTime).then(function (result) {
      const ul = $(el);
      ul.innerHTML = "";
      console.log(result);
      ul.textContent = JSON.stringify(result);
    }.bind(this));
  }

  createMessage(conversationID, content, metadata, el) {
    return this.plugin.createMessage(conversationID, content, metadata).then(function (result) {
      const ul = $(el);
      console.log(result);
      ul.textContent = JSON.stringify(result);
    }.bind(this));
  }
}

