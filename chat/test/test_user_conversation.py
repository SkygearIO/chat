import unittest
from unittest.mock import Mock, patch

from skygear.encoding import deserialize_record
from ..conversation import Conversation
from ..user_conversation import UserConversation


class TestUserConversation(unittest.TestCase):
    def setUp(self):
        self.patchers = [
            patch('chat.utils.skyoptions',
                  Mock(return_value={'masterkey': 'secret'}))
        ]
        for each_patcher in self.patchers:
            each_patcher.start()

    def tearDown(self):
        for each_patcher in self.patchers:
            each_patcher.stop()

    def conversation(self):
        return Conversation.new('conversation1', 'user1')

    def user1(self):
        return 'user1'

    def user2(self):
        return 'user2'

    def test_consistent_hash(self):
        c = self.conversation()
        uc1 = UserConversation.new(c, self.user1())
        uc2 = UserConversation.new(c, self.user1())
        uc3 = UserConversation.new(c, self.user2())
        r1 = uc1.get_hash()
        r2 = uc2.get_hash()
        r3 = uc3.get_hash()
        self.assertEqual(str(r1), str(r2))
        self.assertNotEqual(str(r1), str(r3))
