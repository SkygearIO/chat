from psycopg2.extensions import AsIs

import skygear
from skygear.container import SkygearContainer
from skygear.options import options as skyoptions
from skygear.utils import db

from .field import Field
from .schema import Schema, SchemaHelper
from .utils import _get_schema_name


def register_initialization_event_handlers(settings):
    def _base_message_fields():
        return [Field('attachment', 'asset'),
                Field('body', 'string'),
                Field('metadata', 'json'),
                Field('conversation', 'ref(conversation)'),
                Field('message_status', 'string'),
                Field('seq', 'sequence'),
                Field('revision', 'number'),
                Field('edited_by', 'ref(user)'),
                Field('edited_at', 'datetime')]

    def _message_schema():
        fields = _base_message_fields() + [Field('deleted', 'boolean')]
        return Schema('message', fields)

    def _message_history_schema():
        fields = _base_message_fields() + [Field('parent', 'ref(message)')]
        return Schema('message_history', fields)

    @skygear.event("before-plugins-ready")
    def chat_plugin_init(config):
        container = SkygearContainer(api_key=skyoptions.masterkey)
        schema_helper = SchemaHelper(container)
        # We need this to provision the record type. Otherwise, make the follow
        # up `ref` type will fails.
        schema_helper.create([
            Schema('user', []),
            Schema('message', []),
            Schema('conversation', [])
        ], plugin_request=True)

        conversation_schema = Schema('conversation',
                                     [Field('title', 'string'),
                                      Field('metadata', 'json'),
                                      Field('deleted', 'boolean'),
                                      Field('distinct_by_participants',
                                            'boolean'),
                                      Field('last_message', 'ref(message)')])
        user_schema = Schema('user', [Field('name', 'string')])
        user_conversation_schema = Schema('user_conversation',
                                          [Field('user', 'ref(user)'),
                                           Field('conversation',
                                                 'ref(conversation)'),
                                           Field('unread_count',
                                                 'number'),
                                           Field('last_read_message',
                                                 'ref(message)'),
                                           Field('is_admin',
                                                 'boolean')])
        receipt_schema = Schema('receipt',
                                [Field('user', 'ref(user)'),
                                 Field('message', 'ref(message)'),
                                 Field('read_at', 'datetime'),
                                 Field('delivered_at', 'datetime')])
        user_channel_schema = Schema('user_channel',
                                     [Field('name', 'string')])
        message_schema = _message_schema()
        message_history_schema = _message_history_schema()
        schema_helper.create([user_schema,
                              user_conversation_schema,
                              conversation_schema,
                              message_schema,
                              message_history_schema,
                              receipt_schema,
                              user_channel_schema],
                             plugin_request=True)

        # Create unique constraint to _database_id in user_channel table
        # to ensure there is only one user_channel for each user
        with db.conn() as conn:
            result = conn.execute("""
                select 1
                    FROM information_schema.constraint_column_usage
                WHERE table_schema = '%(schema_name)s'
                    AND table_name = 'user_channel'
                    AND constraint_name = 'user_channel_database_id_key'
                """, {
                    'schema_name': AsIs(_get_schema_name())
                })
            first_row = result.first()
            if first_row is None:
                conn.execute("""
                    DELETE
                        FROM %(schema_name)s.user_channel
                    WHERE _id IN (
                        SELECT _id
                        FROM (
                            SELECT
                                _id,
                                ROW_NUMBER() OVER(
                                    PARTITION BY
                                    _database_id ORDER BY _created_at
                                ) AS row_num
                            FROM  %(schema_name)s.user_channel
                        ) u2 WHERE u2.row_num > 1
                    )
                """, {
                    'schema_name': AsIs(_get_schema_name())
                })
                conn.execute("""
                    ALTER TABLE %(schema_name)s.user_channel
                        ADD CONSTRAINT user_channel_database_id_key
                            UNIQUE (_database_id);
                """, {
                    'schema_name': AsIs(_get_schema_name())
                })
