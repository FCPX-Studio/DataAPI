from fastapi import APIRouter, HTTPException, Query, Request

from app.repositories import ProductRepository
from app.schemas.product import ChangelogEntry, Product, ProductType


# Public and read-only: called server-side by the website (no CORS), cached there for a few minutes
router = APIRouter(
    prefix='/products',
    tags=["products"]
)


def _repository(request: Request) -> ProductRepository:
    return request.app.state.product_repository


@router.get('', response_model=list[Product])
async def list_products(
    request: Request,
    product_type: ProductType | None = Query(None, alias="type", description="Only plugins or assets"),
) -> list[Product]:
    """
    Every product the website may show: not archived, with at least one license on sale
    (free and trial licenses included)

    Args:
        request (Request): Default request argument
        product_type (ProductType | None): `?type=plugin` or `?type=asset`, all products when omitted

    Returns:
        list[Product]: Products ordered by bundle ID, each with its current version and licenses
    """
    return _repository(request).list_products(product_type)


@router.get('/{bundle_id}', response_model=Product)
async def get_product(bundle_id: str, request: Request) -> Product:
    """
    One product, by bundle ID

    Raises:
        HTTPException: 404 unknown product, or not shown (archived, no license on sale)
    """
    product = _repository(request).get_product(bundle_id)
    if product is None:
        raise HTTPException(status_code=404, detail=f"Product '{bundle_id}' not found")
    return product


@router.get('/{bundle_id}/versions', response_model=list[ChangelogEntry])
async def list_versions(bundle_id: str, request: Request) -> list[ChangelogEntry]:
    """
    Changelog of a product: every released version, newest first

    Raises:
        HTTPException: 404 unknown product, or not shown (archived, no license on sale)
    """
    versions = _repository(request).list_versions(bundle_id)
    if versions is None:
        raise HTTPException(status_code=404, detail=f"Product '{bundle_id}' not found")
    return versions
