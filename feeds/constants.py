from model_helpers import Choices


SHARED_WITH = Choices({
    "SELF_DEPARTMENT": 10,
    "ALL_DEPARTMENTS": 20,
    "ADMIN_ONLY": 30,
})

POST_TYPE = Choices({
    "USER_CREATED_POST": 1,
    "USER_CREATED_POLL": 2,
    "SYSTEM_CREATED_POST": 3,
    "MOST_LIKED": 4,
    "MOST_APPRECIATED": 5,
    "USER_CREATED_APPRECIATION": 6,
    "USER_CREATED_NOMINATION": 7,
})

REACTION_TYPE = Choices({
    "LIKE": 0,
    "CELEBRATE": 1,
    "SUPPORT": 2,
    "LOVE": 3,
    "INSIGHTFUL": 4,
    "CURIOUS": 5,
    "APPLAUSE": 6,
})

NOMINATION_STATUS = Choices({
    "NONE": 0,
    "in_review_approver1": 1,
    "in_review_approver2": 2,
    "approved": 3,
    "rejected": 4
})

NOMINATION_STATUS_COLOR_CODE = {
    0: "#FFA412",
    1: "#FFA412",
    2: "#FFA412",
    3: "#40CB57",
    4: "#FF3838",
}