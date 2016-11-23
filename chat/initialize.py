import skygear
from skygear.container import SkygearContainer
from skygear.skyconfig import config as skygear_config


def register_initialization_event_handlers(settings):
    @skygear.event("before-plugins-ready")
    def chat_plugin_init():
        container = SkygearContainer(api_key=skygear_config.app.master_key)
        container.send_action(
            'schema:create',
            {
                'record_types': {
                    'user': {
                        'fields': [
                            {'name': 'name', 'type': 'string'}
                        ]
                    }
                }
            },
            plugin_request=True
        )
        container.send_action(
            'schema:create',
            {
                'record_types': {
                    'conversation': {
                        'fields': [
                            {
                                'name': 'title',
                                'type': 'string'
                            },
                            {
                                'name': 'admin_ids',
                                'type': 'json'
                            },
                            {
                                'name': 'participant_ids',
                                'type': 'json'
                            },
                            {
                                'name': 'participant_count',
                                'type': 'number'
                            },
                            {
                                'name': 'metadata',
                                'type': 'json'
                            },
                            {
                                'name': 'distinct_by_participants',
                                'type': 'boolean'
                            }
                        ]
                    }
                }
            },
            plugin_request=True
        )
        container.send_action(
            'schema:create',
            {
                'record_types': {
                    'message': {
                        'fields': [
                            {
                                'name': 'attachment',
                                'type': 'asset'
                            },
                            {
                                'name': 'body',
                                'type': 'string'
                            },
                            {
                                'name': 'metadata',
                                'type': 'json'
                            },
                            {
                                'name': 'conversation_id',
                                'type': 'ref(conversation)'
                            }
                        ]
                    }
                }
            },
            plugin_request=True
        )
        container.send_action(
            'schema:create',
            {
                'record_types': {
                    'user_conversation': {
                        'fields': [
                            {
                                'name': 'user',
                                'type': 'ref(user)'
                            },
                            {
                                'name': 'conversation',
                                'type': 'ref(conversation)'
                            },
                            {
                                'name': 'unread_count',
                                'type': 'number'
                            },
                            {
                                'name': 'last_read_message',
                                'type': 'ref(message)'
                            }
                        ]
                    }
                }
            },
            plugin_request=True
        )
