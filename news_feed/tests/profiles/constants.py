from __future__ import division, print_function, unicode_literals

from model_helpers import Choices


PLAIN = 0
EVENT = 1
REWARD = 2
SURVEY = 3

UNREAD = 0
READ = 1
DELETE = 2

UNSENT = 0
SENT = 1
ERROR = 2
INACTIVE = 3

NOTIFICATION_OBJECTS = Choices({
    "Plain": PLAIN,
    "Event": EVENT,
    "Reward": REWARD,
    "Survey": SURVEY,
})

NOTIFICATION_STATES = Choices({
    "unread": UNREAD,
    "read": READ,
    "delete": DELETE,
})

NOTIFICATION_STATUS = Choices({
    "unsent": UNSENT,
    "sent": SENT,
    'error': ERROR,
    'inactive': INACTIVE,
})
