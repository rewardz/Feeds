from __future__ import division, print_function, unicode_literals

from model_helpers import Choices


TRANSACTION_STATUSES = Choices({
    "unknown": {"id": 10, "display": "n/a"},
    "pending": {"id": 20, "display": "Pending"},
    "approved": {"id": 30, "display": "Approved"},
    "rejected": {"id": 40, "display": "Rejected"},
    "auto_approved": {"id": 50, "display": "Auto Approved"},
    "benefit_receipt_pending": {"id": 60, "display": "Benefit Receipt Pending"},
})

POINT_SOURCE = Choices({"custom": 0,
                        "facility_checkin": {"id": 1, "display": "Facility Checkin"},
                        "reward_redemption": {"id": 2, "display": "Reward Redemption"},
                        "org_credit": {"id": 3, "display": "Organization Credit"},
                        "delivery_org": {"id": 4, "display": "Reward Delivey to Organization"},
                        "delivery_user": {"id": 5, "display": "Reward Delivey to User"},
                        "strengths": {"id": 6, "display": "Strengths"},
                        })
