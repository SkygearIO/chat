import skygear
from skygear.container import SkygearContainer
from skygear.options import options as skyoptions

from .field import Field
from .schema import Schema, SchemaHelper


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
        receipt_schema = Schema('reeipt',
                                [Field('user', 'ref(user)'),
                                 Field('message', 'ref(message)'),
                                 Field('read_at', 'datetime'),
                                 Field('delivered_at', 'datetime')])
        message_schema = _message_schema()
        message_history_schema = _message_history_schema()
        schema_helper.create([user_schema,
                              user_conversation_schema,
                              conversation_schema,
                              message_schema,
                              message_history_schema,
                              receipt_schema],
                             plugin_request=True)
