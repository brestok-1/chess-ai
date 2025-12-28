"""
Common database requests.
"""

import asyncio
import re
from datetime import timedelta, datetime
from typing import TypeVar

from fastapi import HTTPException
from pydantic import BaseModel

from app.api.common.schemas import (
    SearchRequest,
)
from app.core.config import settings

T = TypeVar("T", bound=BaseModel)

collection_map = {
    "AccountModel": "accounts",
    "AccountShorten": "accounts",
    "ScenarioModel": "scenarios",
    "ScenarioShorten": "scenarios",
    "SessionReportModel": "sessionreports",
    "SessionReportShorten": "sessionreports",
    "TeamModel": "teams",
    "TeamModelShorten": "teams",
    "OrganizationModel": "organizations",
    "OrganizationShorten": "organizations",
    "UserInsightModel": "userinsights",
    "UserInsightShorten": "userinsights",
    "VoiceModel": "voices",
    "VoiceModelShorten": "voices",
    "ActivityLogModel": "activitylogs",
    "AccountNotificationModel": "accountnotifications",
    "FeedbackModel": "generalfeedbacks",
    "FeedbackExtendedModel": "extendedfeedbacks",
    "ScenarioChangeModel": "scenariochanges",
    "WaitlistModel": "waitlists",
    "NotificationModel": "notifications",
    "NotificationModelShorten": "notifications",
}


async def get_obj_by_id(
    model: T,
    obj_id: str | None,
    additional_filter: dict | None = None,
    projection: dict | None = None,
    exception: bool = True,
) -> T | None:
    """
    Get an object by ID.
    """
    filter_ = {"id": obj_id} if obj_id else {}
    if additional_filter:
        filter_.update(additional_filter)
    obj = await settings.DB_CLIENT[collection_map[model.__name__]].find_one(filter_, projection)
    if obj is None:
        if exception:
            raise HTTPException(status_code=404, detail="Object not found.")
        else:
            return None
    return model.from_mongo(obj)


async def get_all_objs(
    model: T,
    page_size: int,
    page_index: int,
    sort: tuple[str, int] = ("id", -1),
    additional_filter: dict | None = None,
    projection: dict | None = None,
) -> tuple[list[T], int]:
    """
    Get all objects.
    """
    filter_ = additional_filter if additional_filter else {}
    skip = page_index * page_size
    objs, total_count = await asyncio.gather(
        settings.DB_CLIENT[collection_map[model.__name__]]
        .find(filter_, projection)
        .sort(*sort)
        .skip(skip)
        .limit(page_size)
        .to_list(page_size),
        settings.DB_CLIENT[collection_map[model.__name__]].count_documents(filter_),
    )
    return [model.from_mongo(obj) for obj in objs], total_count


async def delete_obj(
    model: T, obj_id: str | None = None, additional_filter: dict | None = None
) -> T:
    """
    Delete an object.
    """
    filter_ = {"id": obj_id} if obj_id else {}
    if additional_filter:
        filter_.update(additional_filter)
    obj = await settings.DB_CLIENT[collection_map[model.__name__]].find_one(filter_)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found.")
    await settings.DB_CLIENT[collection_map[model.__name__]].delete_one(filter_)
    return model.from_mongo(obj)


async def search_objs(
    model: T,
    data: SearchRequest,
    additional_filter: dict | None = None,
    projection: dict | None = None,
) -> tuple[list[T], int]:
    """
    Search for objects in a specified collection based on search filters.
    """
    filters = []
    date_filters = {}

    for search_filter in data.filter:
        if isinstance(search_filter.value, str):
            date_match = re.fullmatch(r"^(\d{4}-\d{2}-\d{2});([+-]\d{1,2})$", search_filter.value)

            if date_match:
                if search_filter.name not in date_filters:
                    date_filters[search_filter.name] = []

                date_filters[search_filter.name].append(
                    {
                        "date": datetime.strptime(date_match.group(1), "%Y-%m-%d"),
                        "timezone_offset": int(date_match.group(2)),
                    }
                )
            else:
                filters.append(
                    {
                        search_filter.name: {
                            "$regex": f"^{re.escape(search_filter.value)}",
                            "$options": "i",
                        }
                    }
                )
        else:
            filters.append({search_filter.name: search_filter.value})

    for field_name, dates in date_filters.items():
        if len(dates) == 1:
            date_info = dates[0]
            user_local_day_start = date_info["date"]
            user_local_day_end = user_local_day_start + timedelta(days=1)
            filters.append(
                {
                    field_name: {
                        "$gte": (
                            user_local_day_start - timedelta(hours=date_info["timezone_offset"])
                        ).isoformat(),
                        "$lt": (
                            user_local_day_end - timedelta(hours=date_info["timezone_offset"])
                        ).isoformat(),
                    }
                }
            )
        elif len(dates) == 2:
            start_date = min(dates, key=lambda x: x["date"])
            end_date = max(dates, key=lambda x: x["date"])

            start_datetime = start_date["date"] - timedelta(hours=start_date["timezone_offset"])
            end_datetime = (
                end_date["date"] + timedelta(days=1) - timedelta(hours=end_date["timezone_offset"])
            )

            filters.append(
                {
                    field_name: {
                        "$gte": start_datetime.isoformat(),
                        "$lt": end_datetime.isoformat(),
                    }
                }
            )
        elif len(dates) > 2:
            dates_sorted = sorted(dates, key=lambda x: x["date"])
            start_date = dates_sorted[0]
            end_date = dates_sorted[-1]

            start_datetime = start_date["date"] - timedelta(hours=start_date["timezone_offset"])
            end_datetime = (
                end_date["date"] + timedelta(days=1) - timedelta(hours=end_date["timezone_offset"])
            )

            filters.append(
                {
                    field_name: {
                        "$gte": start_datetime.isoformat(),
                        "$lt": end_datetime.isoformat(),
                    }
                }
            )

    if additional_filter:
        filters.append(additional_filter)
    regex_filter = {"$and": filters} if filters else {}
    objects, total_count = await asyncio.gather(
        settings.DB_CLIENT[collection_map[model.__name__]]
        .find(regex_filter, projection)
        .sort("id", -1)
        .skip(data.pageSize * data.pageIndex)
        .limit(data.pageSize)
        .to_list(length=data.pageSize),
        settings.DB_CLIENT[collection_map[model.__name__]].count_documents(regex_filter),
    )
    return [model.from_mongo(obj) for obj in objects], total_count
