from db import Database
from db.models import ProductLicenseRow, ProductRow, ProductVersionRow

from app.schemas.product import ChangelogEntry, Product, ProductLicense, ProductType, ProductVersion

from sqlalchemy import ColumnElement, and_, exists, select
from sqlalchemy.orm import Session, joinedload, selectinload


# Non-archived licenses of a product, cheapest first (ties: oldest price first, a stable order)
_ACTIVE_LICENSES = ProductRow.licenses.and_(ProductLicenseRow.archived.is_(False))


class ProductRepository(Database):
    """
    Read-only access to the product catalog (written by PaddleSync)
    """

    @staticmethod
    def _visible() -> ColumnElement[bool]:
        """
        The one rule for a product the website may show: not archived, with a current version, and at least
        one non-archived license (free and trial licenses count). Every query of this repository applies it.
        """
        return and_(
            ProductRow.archived.is_(False),
            ProductRow.version_id.is_not(None),
            exists().where(ProductLicenseRow.product_id == ProductRow.id, ProductLicenseRow.archived.is_(False)),
        )

    # --- GET

    def list_products(self, product_type: ProductType | None = None) -> list[Product]:
        """
        Every product the website may show, ordered by bundle ID

        Args:
            product_type (ProductType | None): Only "plugin" or "asset" products, all when None

        Returns:
            list[Product]: Visible products with their current version and non-archived licenses
        """
        stmt = self._products_query()
        if product_type is not None:
            stmt = stmt.where(ProductRow.type == product_type)
        with self.session() as s:
            return [self._to_product(row) for row in s.scalars(stmt.order_by(ProductRow.bundle_id))]

    def get_product(self, bundle_id: str) -> Product | None:
        """
        Args:
            bundle_id (str): Product FxPlug / bundle ID

        Returns:
            Product | None: The product, None if unknown or not visible (archived, no active license...)
        """
        with self.session() as s:
            row = s.scalars(self._products_query().where(ProductRow.bundle_id == bundle_id)).one_or_none()
            return self._to_product(row) if row is not None else None

    def list_versions(self, bundle_id: str) -> list[ChangelogEntry] | None:
        """
        Changelog of a product: every released version, newest first

        Args:
            bundle_id (str): Product FxPlug / bundle ID

        Returns:
            list[ChangelogEntry] | None: Its versions, None if the product is unknown or not visible
        """
        with self.session() as s:
            product_id = self._visible_product_id(s, bundle_id)
            if product_id is None:
                return None
            rows = s.execute(
                select(ProductVersionRow.label, ProductVersionRow.description, ProductVersionRow.release_date)
                .where(ProductVersionRow.product_id == product_id)
                .order_by(ProductVersionRow.release_date.desc(), ProductVersionRow.id.desc())
            ).all()
            return [ChangelogEntry(label=r.label, description=r.description, release_date=r.release_date) for r in rows]

    # --- Helpers

    def _products_query(self):
        """Visible products, with their current version (joined) and active licenses (one extra SELECT)"""
        return (
            select(ProductRow)
            .where(self._visible())
            .options(joinedload(ProductRow.version), selectinload(_ACTIVE_LICENSES))
        )

    def _visible_product_id(self, s: Session, bundle_id: str) -> int | None:
        return s.scalar(select(ProductRow.id).where(ProductRow.bundle_id == bundle_id, self._visible()))

    @staticmethod
    def _to_product(row: ProductRow) -> Product:
        """Build the response inside the session: the relationships are loaded, nothing is lazy-loaded later"""
        version = row.version
        assert version is not None  # guaranteed by _visible()
        licenses = sorted(row.licenses, key=lambda license: (license.price, license.id))
        return Product(
            bundle_id=row.bundle_id,
            name=row.name,
            type=row.type,  # type: ignore[arg-type]  # CHECK (type IN ('plugin', 'asset'))
            version=ProductVersion(
                label=version.label,
                release_date=version.release_date,
                download_path=version.download_path,
                download_size=version.download_size,
            ),
            licenses=[
                ProductLicense(
                    paddle_price_id=license.paddle_price_id,
                    name=license.name,
                    description=license.description,
                    price=license.price,
                    currency_code=license.currency_code,
                    activation_seats=license.activation_seats,
                    life_duration_days=license.life_duration.days if license.life_duration is not None else None,
                    is_trial=license.is_trial,
                )
                for license in licenses
            ],
        )
