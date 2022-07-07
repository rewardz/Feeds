from __future__ import division, print_function, unicode_literals

from model_helpers import Choices

REVIEWER_LEVEL = Choices({
    "NONE": 0,
    "level1": 1,
    "level2": 2,
})

NOMINATION_STATUS = Choices({
    "NONE": 0,
    "in_review_approver1": 1,
    "in_review_approver2": 2,
    "approved": 3,
    "rejected": 4
})
