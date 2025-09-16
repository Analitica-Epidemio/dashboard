"""
Reports router - Report generation endpoints
"""

from fastapi import APIRouter

from .generate import generate_report
from .generate_zip import generate_zip_report
from .preview import preview_report
from .signed_url import generate_report_signed_url, verify_signed_url_endpoint

router = APIRouter(prefix="/reports", tags=["Reports"])

# Generate report endpoint
router.add_api_route(
    "/generate",
    generate_report,
    methods=["POST"]
)

# Generate ZIP report endpoint
router.add_api_route(
    "/generate-zip",
    generate_zip_report,
    methods=["POST"]
)

# Preview report endpoint
router.add_api_route(
    "/preview",
    preview_report,
    methods=["POST"]
)

# Generate signed URL for SSR reports
router.add_api_route(
    "/generate-signed-url",
    generate_report_signed_url,
    methods=["POST"],
    summary="Generate signed URL for SSR reports",
    description="Creates a signed URL that allows access to SSR reports without authentication"
)

# Verify signed URL endpoint
router.add_api_route(
    "/verify-signed-url",
    verify_signed_url_endpoint,
    methods=["POST"],
    summary="Verify signed URL",
    description="Verifies a signed URL and returns the filters data if valid"
)