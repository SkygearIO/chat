/* global describe it before */

'use strict';
const nock = require('nock');
const chai = require('chai');

chai.should();

const skygear = require('skygear');
skygear.configApiKey('my_skygear_key');
const chat = require('../dist/skygear_chat');

function cleanNock() {
  nock.cleanAll();
  nock.disableNetConnect();
}

describe('skygear_chat', function() {
  before(function() {
    nock(skygear.endPoint).post('/auth/login').reply(200, {
      result: {
        user_id: '20bd6d3c-2a94-4932-9df6-fa04765de3f0',
        username: 'lampercy',
        access_token: '4fa9d5a5-8f65-4284-b5f3-f7213c55fcf7'
      }
    });
    return skygear.loginWithUsername('percy', '1234');
  });

  describe('#getChatUser()', function() {
    before(function(done) {
      cleanNock();
      nock(skygear.endPoint).post('/record/query').reply(200, {
        result: [{
          _access: null,
          _created_at: '2016-01-19T08:55:49.563071Z',
          _created_by: '20bd6d3c-2a94-4932-9df6-fa04765de3f0',
          _id: 'chat_user/31bbcf8d-1c63-4e85-b286-31ca29085d93',
          _ownerID: '20bd6d3c-2a94-4932-9df6-fa04765de3f0',
          _type: 'record',
          _updated_at: '2016-01-19T08:55:49.563071Z',
          _updated_by: '20bd6d3c-2a94-4932-9df6-fa04765de3f0'}]
      });
      done();
    });

    it('should return a chat user', function(done) {
      chat.getChatUser().then(
          function(result) {
            result._id.should.equal('31bbcf8d-1c63-4e85-b286-31ca29085d93');
            done();
          }
        );
    });
  });


  describe('#createConversation()', function() {
    before(function(done) {
      cleanNock();
      nock(skygear.endPoint).post('/record/save').reply(200, {
        result: [{ 
          _access: null,
          _created_at: '2016-01-21T06:59:49.794305Z',
          _created_by: '20bd6d3c-2a94-4932-9df6-fa04765de3f0',
          _id: 'conversation/2a2a5ef2-eb58-49bc-aee8-378ffc79f8e4',
          _ownerID: '20bd6d3c-2a94-4932-9df6-fa04765de3f0',
          _type: 'record',
          _updated_at: '2016-01-21T07:00:07.491407Z',
          _updated_by: '20bd6d3c-2a94-4932-9df6-fa04765de3f0',
          admin_ids: [],
          is_direct_message: false,
          metadata: {},
          participant_ids: [],
          title: 'My Title' 
        }] 
      });
      done();
    });

    it('should return a conversation', function(done) {
      chat.createConversation(
          [], [], false, false, "My Title", {}

      ).then(function(result) {
            result._recordType.should.equal('conversation');
            done();
          }
        );
    });
  });

});
