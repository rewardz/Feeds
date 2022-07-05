from model_helpers import Choices


SHARED_WITH = Choices({
    "SELF_DEPARTMENT": 10,
    "ALL_DEPARTMENTS": 20
})

POST_TYPE = Choices({
    "USER_CREATED_POST": 1,
    "USER_CREATED_POLL": 2,
    "SYSTEM_CREATED_POST": 3,
    "MOST_LIKED": 4,
    "MOST_APPRECIATED": 5,
    "FEEDBACK_POST": 6,
})
