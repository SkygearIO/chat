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
    this.directConversationEl = $('direct-conversation')
    this.topbarUsernameEl = $('user-name');
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
    }.bind(this));
  }

  displayCurrentUser() {
    if (skygear.currentUser) {
      this.usernameEl.textContent = skygear.currentUser.username;
      this.emailEl.textContent = skygear.currentUser.email;
      this.tokenEl.textContent = this.container.accessToken;
      this.topbarUsernameEl.textContent = skygear.currentUser.username;
    }
  }

  loginSkygear(username, pw) {
    return this.container.loginWithUsername(username, pw).then(function (result) {
      console.log(result);
      this.displayCurrentUser();
    }.bind(this));
  }

  logoutSkygear() {
    return this.container.logout().then(() => {
      console.log('logout successfully');
      this.usernameEl.textContent = "Not logged in";
      this.emailEl.textContent = "-";
      this.tokenEl.textContent = "";
      this.topbarUsernameEl.textContent = "Not logged in";
    }, (error) => {
      console.log('error logging out', error);
    });
  }

  signupSkygear(username, pw) {
    return this.container.signupWithUsername(username, pw).then(function () {
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

  fetchUserToList(el) {
    const q = new skygear.Query(User);
    return this.container.publicDB.query(q).then(function (result) {
      const ul = $(el);
      ul.innerHTML = "";
      console.log(result);
      for (var item of result) {
        console.log(item);
        var li = document.createElement("li");
        li.innerHTML = ''+item._id+'';
        ul.appendChild(li);
      }
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

  fetchConversationToList(el) {
    return this.plugin.getConversations().then(function (result) {
      const ul = $(el);
      ul.innerHTML = "";
      console.log(result);
      for (var item of result) {
        console.log(item);
        var li = document.createElement("li");
        li.innerHTML = '<a href="message.html?conversation='+item._id+'">'+item._id+'</a>';
        ul.appendChild(li);
      }
    });
  }

  createDirectConversation(userID) {
    // FIXME: the SDK should strip the prefix for me.
    if (userID.startsWith("user/")) {
      userID = userID.substr(5);
    }
    return this.plugin.getOrCreateDirectConversation(userID).then(function (result) {
      console.log(result);
      this.directConversationEl.innerHTML = '<a href="message.html?conversation='+result._id+'">'+result._id+'</a>';
    }.bind(this));
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

