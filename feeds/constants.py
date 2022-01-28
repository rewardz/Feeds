from model_helpers import Choices


SHARED_WITH = Choices({
    "SELF_DEPARTMENT": 10,
    "ALL_DEPARTMENTS": 20
})

POST_TYPE = Choices({
    "USER_CREATED_POST": 1,
    "USER_CREATED_POLL": 2,
    "SYSTEM_CREATED_POST": 3
})

REACTION_TYPE_FOR_FEEDS = Choices({
    "celebrate": 0,
    "curious": 1,
    "insightful": 2,
    "like": 3,
    "love": 4,
    "support": 5,
})
