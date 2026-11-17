"""
Public catalog responses, read by the website (server-side) and any external service.

Only commercial facts synced from Paddle live here. Marketing content (texts, media, order) stays on
the website, joined by `bundle_id`.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ProductType = Literal["plugin", "asset"]


class ProductVersion(BaseModel):
    """Current version of a product, with its download"""
    label: str                                      # e.g. "1.2.0"
    release_date: datetime                          # when PaddleSync first synced this version
    download_path: str                              # relative to the download storage base URL
    download_size: int | None                       # bytes, None if unknown


class ProductLicense(BaseModel):
    """A license on sale (a non-archived Paddle price). Free and trial licenses included"""
    paddle_price_id: str                            # pri_…, opens the Paddle checkout
    name: str                                       # e.g. "2 seats", "Lifetime", "14-day trial"
    description: str | None
    price: int                                      # unit price in minor units (cents), 0 when free
    currency_code: str                              # ISO 4217, e.g. "EUR"
    activation_seats: int                           # machines a license can be activated on
    life_duration_days: int | None                  # trial length for a trial, else license lifetime (None = perpetual)
    is_trial: bool


class Product(BaseModel):
    """A product the website may show (see ProductRepository.visible)"""
    bundle_id: str                                  # FxPlug / bundle ID, the join key with the website content
    name: str
    type: ProductType
    version: ProductVersion
    licenses: list[ProductLicense]                  # never empty, cheapest first


class ChangelogEntry(BaseModel):
    """One released version of a product"""
    label: str
    description: str | None
    release_date: datetime
