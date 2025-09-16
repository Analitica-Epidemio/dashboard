"""
Reports router - Report generation endpoints
"""

from fastapi import APIRouter

from .generate import generate_report
from .generate_zip import generate_zip_report
from .preview import preview_report

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