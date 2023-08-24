from __future__ import division, print_function, unicode_literals

from model_helpers import Choices


###################################################################################################################
# UNPUBLISHED - DEFAULT
# SUBMITTED - Once the feedback is successfully created
# UNDER_REVIEW - Automatically set when the ADMIN responds for the first time
# CLOSED - when Admin marks it as closed.
# AWARDED_CLOSED - Only staff users can change it if the current status is CLOSED
# ERROR - If any exception is raised in processing the request

# Staff member can only update the status i.e. CLOSED, SUBMITTED
###################################################################################################################
FEEDBACK_STATUS_OPTIONS = Choices(
    {
        "UNPUBLISHED": {
            "id": 0,
            "display": "Unpublished",
        },
        "SUBMITTED": {
            "id": 1,
            "display": "Submitted",
        },
        "UNDER_REVIEW": {
            "id": 2,
            "display": "Under Review",
        },
        "CLOSED": {
            "id": 3,
            "display": "Closed",
        },
        "AWARDED_CLOSED": {
            "id": 4,
            "display": "Closed & Awarded",
        },
        "ERROR": {
            "id": 5,
            "display": "Error",
        },
    }
)
