from datetime import datetime

from psycopg2.extensions import AsIs

import skygear
from skygear.encoding import serialize_record
from skygear.models import RecordID, Reference
from skygear.utils import db
from skygear.utils.context import current_user_id

from .asset import sign_asset_url
from .conversation import Conversation
from .exc import (AlreadyDeletedException, ConversationNotFoundException,
                  InvalidGetMessagesConditionArgumentException,
                  MessageNotFoundException, NotInConversationException,
                  NotSupportedException)
from .hooks import (send_after_message_deleted_hook,
                    send_after_message_sent_hook,
                    send_after_message_updated_hook)
from .message import Message
from .message_history import MessageHistory
from .user_conversation import UserConversation
from .utils import _get_schema_name


def __serialize_message_record(message):
    output = serialize_record(message)
    if 'attachment' in output:
        output['attachment'] = output['attachment'].copy()
        output['attachment']['$url'] = \
            sign_asset_url(output['attachment']['$name'])
    return output


def get_messages(conversation_id, limit,
                 before_time=None, before_message_id=None,
                 after_time=None, after_message_id=None,
                 order=None):
    if not Conversation.exists(conversation_id):
        raise ConversationNotFoundException()

    # use message id if given message id as the range condition,
    # otherwise use time as range condition
    #
    # thus if neither message id or time is given, this will return the
    # latest messages
    if before_message_id or after_message_id:
        if before_time or after_time:
            raise InvalidGetMessagesConditionArgumentException()

        return get_messages_by_message(conversation_id, limit,
                                       before_message_id, after_message_id,
                                       order)
    else:
        return get_messages_by_time(conversation_id, limit,
                                    before_time, after_time, order)


def get_messages_by_message(conversation_id, limit,
                            before_message_id=None, after_message_id=None,
                            order=None):
    output = {}
    messages = Message.fetch_all_by_conversation_id(
               conversation_id, limit,
               before_message_id=before_message_id,
               after_message_id=after_message_id,
               order=order)
    output['results'] = [serialize_record(message) for message in messages]

    # include deleted messages in a separate array
    no_limit = 999999

    if len(messages) > 0:
        # if not given both before and after message id
        # assume it is getting latest messages
        #
        # so it does not set before_message_id
        # because we want to get latest deleted messages
        if not after_message_id:
            after_message_id = messages[len(messages) - 1].id.key
        elif not before_message_id:
            before_message_id = messages[0].id.key

    deleted_messages = Message.fetch_all_by_conversation_id(
        conversation_id, no_limit,
        before_message_id=before_message_id,
        after_message_id=after_message_id,
        order=order, deleted=True
    )
    output['deleted'] = \
        [serialize_record(message) for message in deleted_messages]

    return output


def get_messages_by_time(conversation_id, limit,
                         before_time=None, after_time=None, order=None):
    output = {}
    messages = Message.fetch_all_by_conversation_id(
               conversation_id, limit,
               before_time=before_time, after_time=after_time, order=order)
    serialized_messages = [serialize_record(message) for message in messages]
    output['results'] = serialized_messages

    # include deleted messages in a separate array
    no_limit = 999999

    if len(messages) > 0:
        # if not given both before and after time
        # assume it is getting latest messages
        #
        # so it does not set before_time
        # because we want to get latest deleted messages
        if not after_time:
            after_time = serialized_messages[len(messages) - 1]['_created_at']
        elif not before_time:
            before_time = serialized_messages[0]['_created_at']

    deleted_messages = Message.fetch_all_by_conversation_id(
        conversation_id, no_limit,
        before_time=before_time, after_time=after_time, order=order,
        deleted=True
    )
    output['deleted'] = \
        [serialize_record(message) for message in deleted_messages]

    return output


def handle_message_before_save(record, original_record, conn):
    message = Message.from_record(record)

    if original_record is not None and original_record['deleted']:
        raise AlreadyDeletedException()

    if UserConversation.fetch_one(message.conversation_id) is None:
        raise NotInConversationException()

    if original_record is None:
        message['deleted'] = False
        message['revision'] = 1
    else:
        message_history = MessageHistory(Message.from_record(original_record))
        message_history.save()
    message['edited_at'] = datetime.utcnow()
    message['edited_by'] = Reference(RecordID('user', current_user_id()))

    if message.get('message_status', None) is None:
        message['message_status'] = 'delivered'

    # TODO use proper ACL setter
    message._acl = Conversation.get_message_acl(message.conversation_id)
    return serialize_record(message)


def handle_message_after_save(record, original_record, conn):
    message = Message.from_record(record)

    event_type = 'create'
    if original_record is not None:
        event_type = 'update'
    if record.get('deleted', False):
        event_type = 'delete'

    message.notifyParticipants(event_type)
    conversation_id = message.conversation_id
    if original_record is None:
        # Update all UserConversation (except sender) unread count by 1
        conn.execute('''
            UPDATE %(schema_name)s.user_conversation
            SET
                "unread_count" = "unread_count" + 1,
                "_updated_at" = CURRENT_TIMESTAMP
            WHERE
                "conversation" = %(conversation_id)s
                AND "user" != %(user_id)s
        ''', {
            'schema_name': AsIs(_get_schema_name()),
            'conversation_id': conversation_id,
            'user_id': current_user_id()
        })
        # Update all sender's UserConversation
        conn.execute('''
            UPDATE %(schema_name)s.user_conversation
            SET
                "_updated_at" = CURRENT_TIMESTAMP
            WHERE
                "conversation" = %(conversation_id)s
                AND "user" = %(user_id)s
        ''', {
            'schema_name': AsIs(_get_schema_name()),
            'conversation_id': conversation_id,
            'user_id': current_user_id()
        })
        # Update conversation's last message
        conn.execute('''
            UPDATE %(schema_name)s.conversation
            SET
                "last_message" = %(message_id)s,
                "_updated_at" = CURRENT_TIMESTAMP
            WHERE "_id" = %(conversation_id)s
        ''', {
            'schema_name': AsIs(_get_schema_name()),
            'conversation_id': conversation_id,
            'message_id': record.id.key
        })

    conversation = serialize_record(Conversation.fetch_one(conversation_id))
    serialized_message = __serialize_message_record(record)
    participant_ids = conversation['participant_ids']

    if original_record is None:
        send_after_message_sent_hook(serialized_message,
                                     conversation,
                                     participant_ids)
    else:
        send_after_message_updated_hook(serialized_message,
                                        conversation,
                                        participant_ids)


def _get_new_last_message_id(conn, message):
    # TODO rewrite with database.query
    cur = conn.execute('''
            SELECT _id FROM %(schema_name)s.message
            WHERE
                deleted = false AND
                seq < %(seq)s AND
                conversation = %(conversation_id)s
            ORDER BY seq DESC LIMIT 1
        ''', {
            'schema_name': AsIs(_get_schema_name()),
            'seq': message['seq'],
            'conversation_id': message['conversation'].recordID.key
        })
    row = cur.fetchone()
    return None if row is None else row['_id']


def _update_conversation_last_message(conn, conversation, last_message,
                                      new_last_message_id):
    last_message_key = last_message.id.key
    if last_message_key == conversation['last_message_ref'].recordID.key:
        conversation_id = last_message.conversation_id
        conn.execute('''
        UPDATE %(schema_name)s.conversation
        SET last_message = %(new_last_message_id)s
        WHERE _id = %(conversation_id)s
        ''', {
            'schema_name': AsIs(_get_schema_name()),
            'conversation_id': conversation_id,
            'new_last_message_id': new_last_message_id
        })


def _update_user_conversation_last_read_message(conn, last_message,
                                                new_last_message_id):
    conn.execute('''
    UPDATE %(schema_name)s.user_conversation
    SET last_read_message = %(new_last_message_id)s
    WHERE last_read_message = %(old_last_message_id)s
    ''', {
        'schema_name': AsIs(_get_schema_name()),
        'new_last_message_id': new_last_message_id,
        'old_last_message_id': last_message.id.key
    })


def _update_user_conversation_unread_count(conn, deleted_message):
    conn.execute('''
        WITH read_receipt AS (
            SELECT r.user AS read_user
            FROM %(schema_name)s.receipt r
            WHERE r.message = %(message_id)s
            AND read_at IS NOT NULL
        )
        UPDATE %(schema_name)s.user_conversation
        SET unread_count =
        CASE WHEN
            unread_count <= 0
        THEN
            0
        ELSE
            unread_count - 1
        END
        WHERE
            "conversation" = %(conversation_id)s
            AND "user" != %(user_id)s
            AND "user" NOT IN (SELECT read_user FROM read_receipt)
    ''', {
        'schema_name': AsIs(_get_schema_name()),
        'conversation_id': deleted_message.conversation_id,
        'message_id': deleted_message.id.key,
        'user_id': deleted_message.owner_id
    })


def delete_message(message_id):
    '''
    Delete a message
    - Soft-delete message from record
    - Update last_message and last_read_message
    '''
    message = Message.fetch_one(message_id)
    if message is None:
        raise MessageNotFoundException()

    message.delete()
    record = serialize_record(message)
    conversation = Conversation.fetch_one(message.conversation_id)

    with db.conn() as conn:
        new_last_message_id = _get_new_last_message_id(conn, message)
        _update_conversation_last_message(conn, conversation, message,
                                          new_last_message_id)
        _update_user_conversation_last_read_message(conn, message,
                                                    new_last_message_id)
        _update_user_conversation_unread_count(conn, message)

    serialized_conversation = serialize_record(conversation)
    participant_ids = serialized_conversation['participant_ids']
    serialized_message = __serialize_message_record(message)
    send_after_message_deleted_hook(serialized_message,
                                    serialized_conversation,
                                    participant_ids)
    return record


def register_message_hooks(settings):
    @skygear.before_save("message", async=False)
    def message_before_save_handler(record, original_record, conn):
        return handle_message_before_save(record, original_record, conn)

    @skygear.after_save("message")
    def message_after_save_handler(record, original_record, conn):
        return handle_message_after_save(record, original_record, conn)

    @skygear.before_delete("message", async=False)
    def message_before_delete_handler(record, conn):
        raise NotSupportedException()


def register_message_lambdas(settings):
    @skygear.op("chat:get_messages", auth_required=True, user_required=True)
    def get_messages_lambda(conversation_id, limit,
                            before_time=None, order=None,
                            before_message_id=None, after_time=None,
                            after_message_id=None):
        return get_messages(conversation_id, limit,
                            before_time, before_message_id,
                            after_time, after_message_id,
                            order)

    @skygear.op("chat:delete_message", auth_required=True, user_required=True)
    def delete_message_lambda(message_id):
        return delete_message(message_id)
