from __future__ import division, print_function, unicode_literals

from model_helpers import Choices

REVIEWER_LEVEL = Choices({
    "none": 0,
    "level1": 1,
    "level2": 2,
})

NOMINATION_STATUS = Choices({
    "submitted": 0,
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
