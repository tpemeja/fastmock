"""
Module containing the Device model definition.
"""

from typing import ClassVar
from datetime import date
from pydantic import BaseModel, Field, EmailStr


class Coordinate(BaseModel):
    """
    Represents a geographical coordinate with latitude and longitude.

    Attributes:
    - latitude (float): The latitude in decimal degrees, must be between -90 and 90.
    - longitude (float): The longitude in decimal degrees, must be between -180 and 180.
    """
    latitude: float = Field(default=...,
                            description="Latitude in decimal degrees. "
                                        "Must be between -90 and 90.")
    longitude: float = Field(default=...,
                             description="Longitude in decimal degrees. "
                                         "Must be between -180 and 180.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "latitude": 35.6582,
                "longitude": 139.8752
            }
        }
    }


class Device(BaseModel):
    """
    Represents a device with unique identifiers and location information.

    Attributes:
    - device_uuid (str): The UUID of the device. It should start with the prefix (DEV),
      followed by a single uppercase letter and six digits (e.g., DEVX000001).
    - localisation (Coordinate): Geographical location of the device as coordinates.
    - deployment_date (date): The deployment date of the device in the format YYYY-MM-DD.
    - owner (EmailStr): The email address of the owner of the device.
    """
    UUID_REGEX_PATTERN: ClassVar[str] = r'^DEV[A-Z]\d{6}$'

    device_uuid: str = Field(default=...,
                             description="The UUID of the device. "
                                         "It should start with the prefix (DEV), "
                                         "a single uppercase letter, "
                                         "and six digits (e.g., DEVX000001)")

    localisation: Coordinate = Field(default=None,
                                     description="The geographical location of the device "
                                                 "as latitude and longitude coordinates")

    deployment_date: date = Field(default=None,
                                  description="The deployment date of the device "
                                              "in the format YYYY-MM-DD")
    owner: EmailStr = Field(default=...,
                            description="The email address of the owner of the device")

    model_config = {
        "json_schema_extra": {
            "example": {
                "device_uuid": "DEVX000001",
                "localisation": {
                    "latitude": 35.6582,
                    "longitude": 139.8752
                },
                "deployment_date": "2024-03-14",
                "owner": "tanguy.pemeja@gmail.com"
            }
        }
    }


class DeviceNotFoundResponse(BaseModel):
    """
    Represents a response indicating that the device was not found.
    """
    message: str = "Device not found"


class DeviceAlreadyExists(BaseModel):
    """
    Represents a response indicating that the device already exists.
    """
    message: str = "Device already exists"
