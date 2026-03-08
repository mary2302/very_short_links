"""Link service for managing shortened URLs."""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy import select, delete, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.link import Link
from src.models.user import User
from src.schemas.link import LinkCreate, LinkUpdate
from src.utils.short_code import generate_short_code
from src.services.cache_service import CacheService

settings = get_settings()


class LinkService:
    """Service for link management operations."""
    
    def __init__(self, db: AsyncSession, cache: CacheService):
        """Initialize link service."""
        self.db = db
        self.cache = cache
    
    async def create_link(
        self,
        link_data: LinkCreate,
        owner: Optional[User] = None,
        base_url: str = "http://localhost:8000"
    ) -> Link:
        """Create a new shortened link."""
        # Generate unique short code
        short_code = generate_short_code()
        
        # Check if custom alias is unique
        if link_data.custom_alias:
            existing = await self.get_link_by_code(link_data.custom_alias)
            if existing:
                raise ValueError("Custom alias already exists")
        
        # Ensure short code is unique
        while await self.get_link_by_code(short_code):
            short_code = generate_short_code()
        
        link = Link(
            original_url=link_data.original_url,
            short_code=short_code,
            custom_alias=link_data.custom_alias,
            expires_at=link_data.expires_at,
            project=link_data.project,
            owner_id=owner.id if owner else None,
        )
        
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        
        # Cache the link
        await self.cache_link(link, base_url)
        
        return link
    
    async def get_link_by_code(self, code: str) -> Optional[Link]:
        """Get link by short code or custom alias."""
        # Try cache first
        cached = await self.cache.get_link(code)
        if cached:
            # Still need to get from DB for full object
            pass
        
        result = await self.db.execute(
            select(Link).where(
                or_(Link.short_code == code, Link.custom_alias == code)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_link_by_id(self, link_id: int) -> Optional[Link]:
        """Get link by ID."""
        result = await self.db.execute(select(Link).where(Link.id == link_id))
        return result.scalar_one_or_none()
    
    async def get_original_url(self, code: str, base_url: str = "http://localhost:8000") -> Optional[str]:
        """Get original URL and update statistics."""
        # Try cache first
        cached = await self.cache.get_link(code)
        if cached:
            original_url = cached.get("original_url")
            # Update click count in cache
            await self.cache.increment_click_count(code)
            # Update DB asynchronously
            link = await self.get_link_by_code(code)
            if link and not link.is_expired and link.is_active:
                link.click_count += 1
                link.last_accessed_at = datetime.now(timezone.utc)
                await self.db.commit()
                return original_url
        
        link = await self.get_link_by_code(code)
        if link is None:
            return None
        
        if link.is_expired or not link.is_active:
            return None
        
        # Update statistics
        link.click_count += 1
        link.last_accessed_at = datetime.now(timezone.utc)
        await self.db.commit()
        
        # Cache for future requests
        await self.cache_link(link, base_url)
        
        return link.original_url
    
    async def update_link(
        self,
        code: str,
        link_data: LinkUpdate,
        user: User
    ) -> Optional[Link]:
        """Update a link (only by owner)."""
        link = await self.get_link_by_code(code)
        if link is None:
            return None
        
        # Check ownership
        if link.owner_id != user.id:
            raise PermissionError("You don't have permission to update this link")
        
        # Update fields
        if link_data.original_url is not None:
            link.original_url = link_data.original_url
        
        if link_data.custom_alias is not None:
            # Check if new alias is unique
            existing = await self.get_link_by_code(link_data.custom_alias)
            if existing and existing.id != link.id:
                raise ValueError("Custom alias already exists")
            link.custom_alias = link_data.custom_alias
        
        if link_data.expires_at is not None:
            link.expires_at = link_data.expires_at
        
        if link_data.project is not None:
            link.project = link_data.project
        
        link.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(link)
        
        # Invalidate and update cache
        await self.cache.delete_link(code)
        
        return link
    
    async def delete_link(self, code: str, user: User) -> bool:
        """Delete a link (only by owner)."""
        link = await self.get_link_by_code(code)
        if link is None:
            return False
        
        # Check ownership
        if link.owner_id != user.id:
            raise PermissionError("You don't have permission to delete this link")
        
        # Delete from cache
        await self.cache.delete_link(code)
        if link.custom_alias:
            await self.cache.delete_link(link.custom_alias)
        
        await self.db.delete(link)
        await self.db.commit()
        return True
    
    async def search_by_original_url(self, original_url: str) -> List[Link]:
        """Search links by original URL."""
        result = await self.db.execute(
            select(Link).where(
                Link.original_url == original_url,
                Link.is_active == True
            )
        )
        return result.scalars().all()
    
    async def get_link_stats(self, code: str) -> Optional[Link]:
        """Get link statistics."""
        link = await self.get_link_by_code(code)
        if link is None:
            return None
        return link
    
    async def get_user_links(self, user: User, skip: int = 0, limit: int = 100) -> List[Link]:
        """Get all links for a user."""
        result = await self.db.execute(
            select(Link)
            .where(Link.owner_id == user.id)
            .offset(skip)
            .limit(limit)
            .order_by(Link.created_at.desc())
        )
        return result.scalars().all()
    
    async def cleanup_expired_links(self) -> int:
        """Remove expired links from database."""
        result = await self.db.execute(
            delete(Link).where(
                Link.expires_at.isnot(None),
                Link.expires_at < datetime.now(timezone.utc)
            )
        )
        await self.db.commit()
        return result.rowcount
    
    async def cleanup_unused_links(self, days: Optional[int] = None) -> int:
        """Remove links unused for specified days."""
        if days is None:
            days = settings.unused_link_cleanup_days
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await self.db.execute(
            delete(Link).where(
                or_(
                    Link.last_accessed_at < cutoff_date,
                    and_(Link.last_accessed_at.is_(None), Link.created_at < cutoff_date)
                )
            )
        )
        await self.db.commit()
        return result.rowcount
    
    async def get_expired_links_history(self, skip: int = 0, limit: int = 100) -> List[Link]:
        """Get history of expired links."""
        result = await self.db.execute(
            select(Link)
            .where(
                Link.expires_at.isnot(None),
                Link.expires_at < datetime.now(timezone.utc)
            )
            .offset(skip)
            .limit(limit)
            .order_by(Link.expires_at.desc())
        )
        return result.scalars().all()
    
    async def get_links_by_project(self, project: str, user: Optional[User] = None) -> List[Link]:
        """Get links grouped by project."""
        query = select(Link).where(Link.project == project, Link.is_active == True)
        if user:
            query = query.where(Link.owner_id == user.id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def cache_link(self, link: Link, base_url: str):
        """Cache link data in Redis."""
        effective_code = link.custom_alias or link.short_code
        link_data = {
            "id": link.id,
            "original_url": link.original_url,
            "short_code": link.short_code,
            "custom_alias": link.custom_alias,
            "short_url": f"{base_url}/{effective_code}",
            "click_count": link.click_count,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        }
        # Cache for 1 hour
        await self.cache.set_link(effective_code, link_data, expire=3600)
