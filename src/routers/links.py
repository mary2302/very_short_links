"""Links router for URL shortening operations."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.schemas.link import LinkCreate, LinkUpdate, LinkResponse, LinkStats, LinkSearchResult
from src.services.link_service import LinkService
from src.services.cache_service import get_cache_service, CacheService
from src.services.auth_service import current_active_user, current_user_optional
from src.utils.url_helpers import get_base_url

router = APIRouter(prefix="/links", tags=["Links"])


def get_link_service(
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
) -> LinkService:
    """Dependency for LinkService."""
    return LinkService(db, cache)


def link_to_response(link, base_url: str) -> LinkResponse:
    """Convert Link model to LinkResponse."""
    effective_code = link.custom_alias or link.short_code
    return LinkResponse(
        id=link.id,
        original_url=link.original_url,
        short_code=link.short_code,
        custom_alias=link.custom_alias,
        short_url=f"{base_url}/{effective_code}",
        created_at=link.created_at,
        expires_at=link.expires_at,
        is_active=link.is_active,
        project=link.project,
        owner_id=link.owner_id,
    )


@router.post("/shorten", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_short_link(
    link_data: LinkCreate,
    request: Request,
    current_user: Optional[User] = Depends(current_user_optional),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Create a shortened URL.
    
    - **original_url**: The original URL to shorten (required)
    - **custom_alias**: Optional custom short code
    - **expires_at**: Optional expiration datetime
    - **project**: Optional project name for grouping
    
    Works for both authenticated and anonymous users.
    """
    base_url = get_base_url(request)
    
    try:
        link = await link_service.create_link(link_data, current_user, base_url)
        return link_to_response(link, base_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/search", response_model=LinkSearchResult)
async def search_links(
    original_url: str = Query(..., description="Original URL to search for"),
    request: Request = None,
    link_service: LinkService = Depends(get_link_service)
):
    """
    Search for links by original URL.
    
    - **original_url**: The original URL to search for
    """
    base_url = get_base_url(request)
    
    links = await link_service.search_by_original_url(original_url)
    return LinkSearchResult(
        links=[link_to_response(link, base_url) for link in links],
        total=len(links)
    )


@router.get("/{short_code}/stats", response_model=LinkStats)
async def get_link_stats(
    short_code: str,
    link_service: LinkService = Depends(get_link_service)
):
    """
    Get statistics for a shortened link.
    
    - **short_code**: The short code or custom alias
    
    Returns:
    - Original URL
    - Creation date
    - Click count
    - Last accessed date
    """
    link = await link_service.get_link_stats(short_code)
    
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    
    return LinkStats(
        id=link.id,
        original_url=link.original_url,
        short_code=link.short_code,
        custom_alias=link.custom_alias,
        click_count=link.click_count,
        created_at=link.created_at,
        last_accessed_at=link.last_accessed_at,
        expires_at=link.expires_at,
        is_active=link.is_active,
        project=link.project,
    )


@router.put("/{short_code}", response_model=LinkResponse)
async def update_link(
    short_code: str,
    link_data: LinkUpdate,
    request: Request,
    current_user: User = Depends(current_active_user),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Update a shortened link.
    
    Requires authentication. Only the link owner can update.
    
    - **original_url**: New original URL (optional)
    - **custom_alias**: New custom alias (optional)
    - **expires_at**: New expiration datetime (optional)
    - **project**: New project name (optional)
    """
    base_url = get_base_url(request)
    
    try:
        link = await link_service.update_link(short_code, link_data, current_user)
        if link is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        return link_to_response(link, base_url)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    short_code: str,
    current_user: User = Depends(current_active_user),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Delete a shortened link.
    
    Requires authentication. Only the link owner can delete.
    """
    try:
        deleted = await link_service.delete_link(short_code, current_user)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/user/my-links", response_model=List[LinkResponse])
async def get_my_links(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(current_active_user),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Get all links created by the current user.
    
    Requires authentication.
    """
    base_url = get_base_url(request)
    
    links = await link_service.get_user_links(current_user, skip, limit)
    return [link_to_response(link, base_url) for link in links]


@router.get("/project/{project}", response_model=List[LinkResponse])
async def get_links_by_project(
    project: str,
    request: Request,
    current_user: Optional[User] = Depends(current_user_optional),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Get all links in a project.
    
    If authenticated, returns only user's links in the project.
    """
    base_url = get_base_url(request)
    
    links = await link_service.get_links_by_project(project, current_user)
    return [link_to_response(link, base_url) for link in links]


@router.post("/admin/cleanup/expired", tags=["Admin"])
async def cleanup_expired(
    current_user: User = Depends(current_active_user),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Remove expired links from database.
    
    Requires authentication. (In production, should be admin-only)
    """
    deleted = await link_service.cleanup_expired_links()
    return {"deleted": deleted, "message": f"Deleted {deleted} expired links"}


@router.post("/admin/cleanup/unused", tags=["Admin"])
async def cleanup_unused(
    days: int = Query(90, ge=1, description="Days of inactivity threshold"),
    current_user: User = Depends(current_active_user),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Remove links unused for specified days.
    
    Requires authentication. (In production, should be admin-only)
    """
    deleted = await link_service.cleanup_unused_links(days)
    return {"deleted": deleted, "message": f"Deleted {deleted} unused links"}


@router.get("/admin/expired-history", response_model=List[LinkStats], tags=["Admin"])
async def get_expired_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(current_active_user),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Get history of expired links.
    
    Requires authentication. (In production, should be admin-only)
    """
    links = await link_service.get_expired_links_history(skip, limit)
    return [
        LinkStats(
            id=link.id,
            original_url=link.original_url,
            short_code=link.short_code,
            custom_alias=link.custom_alias,
            click_count=link.click_count,
            created_at=link.created_at,
            last_accessed_at=link.last_accessed_at,
            expires_at=link.expires_at,
            is_active=link.is_active,
            project=link.project,
        )
        for link in links
    ]
