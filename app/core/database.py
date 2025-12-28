"""
Database utilities for ClipboardHealthAI application.
"""

from datetime import datetime
from enum import Enum
import re
from typing import Any, Dict, Type, TypeVar

from bson import ObjectId
from pydantic import AnyUrl, BaseModel, Field, GetCoreSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

T = TypeVar("T", bound=BaseModel)


class PyObjectId:
    """
    Custom type for handling MongoDB ObjectId in Pydantic models.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Define the core schema for Pydantic validation.
        """
        return core_schema.with_info_after_validator_function(
            cls.validate, core_schema.str_schema()  # type: ignore
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _schema: core_schema.CoreSchema, _handler: GetCoreSchemaHandler
    ) -> JsonSchemaValue:
        """
        Define the JSON schema representation.
        """
        return {"type": "string"}

    @classmethod
    def validate(cls, value: str) -> ObjectId:
        """
        Validate and convert a string to MongoDB ObjectId.
        """
        if not ObjectId.is_valid(value):
            raise ValueError(f"Invalid ObjectId: {value}")
        return ObjectId(value)

    def __getattr__(self, item):
        """
        Delegate attribute access to the wrapped ObjectId.
        """
        return getattr(self.__dict__["value"], item)

    def __init__(self, value: str | None = None):
        """
        Initialize with a string value or create a new ObjectId.
        """
        if value is None:
            self.value = ObjectId()
        else:
            self.value = self.validate(value)

    def __str__(self):
        """
        Convert to string representation.
        """
        return str(self.value)


class MongoBaseModel(BaseModel):
    """
    Base model for MongoDB documents with serialization support.
    """

    id: str = Field(default_factory=lambda: str(PyObjectId()))

    class Config:  # pylint: disable=R0903
        """
        Configuration for the model.
        """

        arbitrary_types_allowed = True
        extra = "ignore"
        populate_by_name = True

    @staticmethod
    def serialize_s3_url(value: Any) -> Any:
        """
        Serialize an S3 URL.
        """
        if value and isinstance(value, str) and "AWSAccessKeyId" in value and "Expires" in value:
            match = re.search(r"s3\.amazonaws\.com/([^?]+)", value)
            if match:
                return match.group(1)
        return value

    def to_mongo(self) -> Dict[str, Any]:
        """
        Convert the model instance to a MongoDB-compatible dictionary.
        """

        def model_to_dict(model: BaseModel) -> Dict[str, Any]:
            doc = {}
            for name in model.__fields__.keys():
                value = getattr(model, name)
                key = model.__fields__[name].alias or name

                if isinstance(value, BaseModel):
                    doc[key] = model_to_dict(value)
                elif isinstance(value, list) and all(isinstance(i, BaseModel) for i in value):
                    doc[key] = [model_to_dict(item) for item in value]  # type: ignore
                elif value and isinstance(value, Enum):
                    doc[key] = value.value
                elif isinstance(value, datetime):
                    doc[key] = value.isoformat()  # type: ignore
                elif value and isinstance(value, AnyUrl):
                    doc[key] = str(value)  # type: ignore
                else:
                    doc[key] = self.serialize_s3_url(value)

            return doc

        result = model_to_dict(self)
        return result

    @classmethod
    def from_mongo(cls, data: Dict[str, Any]):
        """
        Create a model instance from MongoDB document data.
        """

        def restore_enums(inst: Any, model_cls: Type[BaseModel]) -> None:
            for name, field in model_cls.__fields__.items():  # type: ignore
                value = getattr(inst, name)
                if (
                    field
                    and isinstance(field.annotation, type)
                    and issubclass(field.annotation, Enum)
                ):
                    setattr(inst, name, field.annotation(value))
                elif isinstance(value, BaseModel):
                    restore_enums(value, value.__class__)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, BaseModel):
                            restore_enums(item, item.__class__)
                        elif isinstance(field.annotation, type) and issubclass(
                            field.annotation, Enum
                        ):
                            value[i] = field.annotation(item)
                elif isinstance(value, dict):
                    for k, v in value.items():
                        if isinstance(v, BaseModel):
                            restore_enums(v, v.__class__)
                        elif isinstance(field.annotation, type) and issubclass(
                            field.annotation, Enum
                        ):
                            value[k] = field.annotation(v)

        if data is None:
            return None
        instance = cls(**data)
        restore_enums(instance, instance.__class__)
        return instance


class MongoBaseShortenModel(BaseModel):
    """
    Base model for MongoDB documents with serialization support.
    """

    id: str

    @classmethod
    def to_mongo_fields(self) -> dict:
        result = {field: 1 for field in self.__annotations__ if field != "_id"}
        result["_id"] = 0
        result['id'] = 1
        return result

    @classmethod
    def from_mongo(cls, mongo_obj: Dict[str, Any]) -> T:
        return cls(**mongo_obj)
