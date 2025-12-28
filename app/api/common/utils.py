"""
Common utilities.
"""

from cbh.api.account.dto import AccountType
from cbh.api.account.models import AccountModel
from cbh.api.scenario.dto import AssigneesType


def form_additional_scenario_filter(account: AccountModel):
    filter_ = {"owner.organization.id": account.organization.id}
    if account.accountType == AccountType.USER:
        filter_.update(
            {
                "$or": [
                    {"assignees": {"$size": 0}},
                    {
                        "assignees": {
                            "$elemMatch": {
                                "type": AssigneesType.USER.value,
                                "account.id": account.id,
                            }
                        }
                    },
                    {
                        "assignees": {
                            "$elemMatch": {
                                "type": AssigneesType.TEAM.value,
                                "team.members": {"$elemMatch": {"id": account.id}},
                            }
                        }
                    },
                ],
            }
        )
    return filter_
