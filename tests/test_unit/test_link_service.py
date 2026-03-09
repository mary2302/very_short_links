"""Unit tests for LinkService."""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.link_service import LinkService
from src.schemas.link import LinkCreate, LinkUpdate
from src.models.link import Link
from src.models.user import User


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_cache():
    """Create mock cache service."""
    cache = MagicMock()
    cache.get_link = AsyncMock(return_value=None)
    cache.set_link = AsyncMock(return_value=True)
    cache.delete_link = AsyncMock(return_value=1)
    cache.increment_click_count = AsyncMock(return_value=1)
    cache.set_json = AsyncMock(return_value=True)
    cache.get_json = AsyncMock(return_value=None)
    return cache


@pytest.fixture
def link_service(mock_db, mock_cache):
    """Create LinkService with mocked dependencies."""
    return LinkService(mock_db, mock_cache)


class TestLinkServiceCreate:
    """Tests for link creation in LinkService."""
    
    @pytest.mark.asyncio
    async def test_create_link_basic(self, link_service, mock_db):
        """Test creating a basic link."""
        # Mock the execute to return None (no existing link)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        link_data = LinkCreate(original_url="https://example.com/test")
        link = await link_service.create_link(link_data, owner=None)
        
        assert link is not None
        assert link.original_url == "https://example.com/test"
        assert link.short_code is not None
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_link_with_custom_alias(self, link_service, mock_db):
        """Test creating link with custom alias."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        link_data = LinkCreate(
            original_url="https://example.com/custom",
            custom_alias="my-alias"
        )
        link = await link_service.create_link(link_data, owner=None)
        
        assert link.custom_alias == "my-alias"
    
    @pytest.mark.asyncio
    async def test_create_link_with_expiry(self, link_service, mock_db):
        """Test creating link with expiration."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        link_data = LinkCreate(
            original_url="https://example.com/expiring",
            expires_at=expires
        )
        link = await link_service.create_link(link_data, owner=None)
        
        assert link.expires_at == expires
    
    @pytest.mark.asyncio
    async def test_create_link_with_project(self, link_service, mock_db):
        """Test creating link with project."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        link_data = LinkCreate(
            original_url="https://example.com/project",
            project="my-project"
        )
        link = await link_service.create_link(link_data, owner=None)
        
        assert link.project == "my-project"
    
    @pytest.mark.asyncio
    async def test_create_link_with_owner(self, link_service, mock_db):
        """Test creating link with owner."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        owner = MagicMock(spec=User)
        owner.id = uuid.uuid4()
        
        link_data = LinkCreate(original_url="https://example.com/owned")
        link = await link_service.create_link(link_data, owner=owner)
        
        assert link.owner_id == owner.id


class TestLinkServiceGet:
    """Tests for getting links in LinkService."""
    
    @pytest.mark.asyncio
    async def test_get_link_by_code(self, link_service, mock_db, mock_cache):
        """Test getting link by short code."""
        expected_link = Link(
            id=1,
            original_url="https://example.com",
            short_code="abc123",
            is_active=True
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_link
        mock_db.execute.return_value = mock_result
        
        link = await link_service.get_link_by_code("abc123")
        
        assert link == expected_link
    
    @pytest.mark.asyncio
    async def test_get_link_not_found(self, link_service, mock_db, mock_cache):
        """Test getting non-existent link."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        link = await link_service.get_link_by_code("nonexistent")
        
        assert link is None


class TestLinkServiceGetOriginalUrl:
    """Tests for get_original_url method."""
    
    @pytest.mark.asyncio
    async def test_get_original_url_from_cache(self, link_service, mock_db, mock_cache):
        """Test getting URL when data is cached."""
        cached_data = {"original_url": "https://cached.example.com"}
        mock_cache.get_link.return_value = cached_data
        
        # Mock DB link (for cache hit path)
        db_link = Link(
            id=1,
            original_url="https://cached.example.com",
            short_code="cached123",
            is_active=True,
            expires_at=None,
            click_count=10
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = db_link
        mock_db.execute.return_value = mock_result
        
        result = await link_service.get_original_url("cached123", "http://test.com")
        
        assert result == "https://cached.example.com"
        mock_cache.get_link.assert_called_with("cached123")
        mock_cache.increment_click_count.assert_called_with("cached123")
        assert db_link.click_count == 11  # Incremented
    
    @pytest.mark.asyncio
    async def test_get_original_url_not_in_cache(self, link_service, mock_db, mock_cache):
        """Test getting URL from DB when not cached."""
        mock_cache.get_link.return_value = None
        
        db_link = Link(
            id=1,
            original_url="https://db.example.com",
            short_code="db123",
            is_active=True,
            expires_at=None,
            click_count=5
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = db_link
        mock_db.execute.return_value = mock_result
        
        result = await link_service.get_original_url("db123", "http://test.com")
        
        assert result == "https://db.example.com"
        assert db_link.click_count == 6  # Incremented
    
    @pytest.mark.asyncio
    async def test_get_original_url_link_not_found(self, link_service, mock_db, mock_cache):
        """Test getting URL for non-existent link."""
        mock_cache.get_link.return_value = None
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        result = await link_service.get_original_url("notfound", "http://test.com")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_original_url_expired_link(self, link_service, mock_db, mock_cache):
        """Test getting URL for expired link."""
        mock_cache.get_link.return_value = None
        
        expired_link = Link(
            id=1,
            original_url="https://expired.example.com",
            short_code="exp123",
            is_active=True,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expired_link
        mock_db.execute.return_value = mock_result
        
        result = await link_service.get_original_url("exp123", "http://test.com")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_original_url_inactive_link(self, link_service, mock_db, mock_cache):
        """Test getting URL for inactive link."""
        mock_cache.get_link.return_value = None
        
        inactive_link = Link(
            id=1,
            original_url="https://inactive.example.com",
            short_code="inactive123",
            is_active=False
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inactive_link
        mock_db.execute.return_value = mock_result
        
        result = await link_service.get_original_url("inactive123", "http://test.com")
        
        assert result is None


class TestLinkServiceUpdate:
    """Tests for updating links in LinkService."""
    
    @pytest.mark.asyncio
    async def test_update_link(self, link_service, mock_db, mock_cache):
        """Test updating a link."""
        owner_id = uuid.uuid4()
        existing_link = Link(
            id=1,
            original_url="https://old.example.com",
            short_code="update123",
            is_active=True,
            owner_id=owner_id
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_link
        mock_db.execute.return_value = mock_result
        
        user = MagicMock(spec=User)
        user.id = owner_id
        
        update_data = LinkUpdate(original_url="https://new.example.com")
        updated = await link_service.update_link("update123", update_data, user)
        
        assert updated.original_url == "https://new.example.com"
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_update_link_not_owner(self, link_service, mock_db, mock_cache):
        """Test updating link by non-owner raises PermissionError."""
        owner_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        
        existing_link = Link(
            id=1,
            original_url="https://old.example.com",
            short_code="update123",
            is_active=True,
            owner_id=owner_id
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_link
        mock_db.execute.return_value = mock_result
        
        user = MagicMock(spec=User)
        user.id = other_user_id  # Different from owner
        
        update_data = LinkUpdate(original_url="https://new.example.com")
        
        with pytest.raises(PermissionError):
            await link_service.update_link("update123", update_data, user)
    
    @pytest.mark.asyncio
    async def test_update_link_duplicate_alias(self, link_service, mock_db, mock_cache):
        """Test updating link with duplicate alias raises ValueError."""
        owner_id = uuid.uuid4()
        
        existing_link = Link(
            id=1,
            original_url="https://old.example.com",
            short_code="update123",
            is_active=True,
            owner_id=owner_id
        )
        
        # Another link with the alias we want to use
        alias_link = Link(
            id=2,
            original_url="https://other.example.com",
            short_code="other123",
            custom_alias="taken-alias",
            is_active=True
        )
        
        mock_result = MagicMock()
        # First call returns the link to update, second call returns the existing alias
        mock_result.scalar_one_or_none.side_effect = [existing_link, alias_link]
        mock_db.execute.return_value = mock_result
        
        user = MagicMock(spec=User)
        user.id = owner_id
        
        update_data = LinkUpdate(custom_alias="taken-alias")
        
        with pytest.raises(ValueError, match="already exists"):
            await link_service.update_link("update123", update_data, user)
    
    @pytest.mark.asyncio
    async def test_update_link_with_project(self, link_service, mock_db, mock_cache):
        """Test updating link project field."""
        owner_id = uuid.uuid4()
        existing_link = Link(
            id=1,
            original_url="https://old.example.com",
            short_code="update123",
            is_active=True,
            owner_id=owner_id
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_link
        mock_db.execute.return_value = mock_result
        
        user = MagicMock(spec=User)
        user.id = owner_id
        
        update_data = LinkUpdate(project="new-project")
        updated = await link_service.update_link("update123", update_data, user)
        
        assert updated.project == "new-project"
    
    @pytest.mark.asyncio
    async def test_update_link_with_expires(self, link_service, mock_db, mock_cache):
        """Test updating link expiration."""
        owner_id = uuid.uuid4()
        existing_link = Link(
            id=1,
            original_url="https://old.example.com",
            short_code="update123",
            is_active=True,
            owner_id=owner_id
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_link
        mock_db.execute.return_value = mock_result
        
        user = MagicMock(spec=User)
        user.id = owner_id
        
        new_expires = datetime.now(timezone.utc) + timedelta(days=30)
        update_data = LinkUpdate(expires_at=new_expires)
        updated = await link_service.update_link("update123", update_data, user)
        
        assert updated.expires_at == new_expires


class TestLinkServiceDelete:
    """Tests for deleting links in LinkService."""
    
    @pytest.mark.asyncio
    async def test_delete_link(self, link_service, mock_db, mock_cache):
        """Test deleting a link."""
        owner_id = uuid.uuid4()
        existing_link = Link(
            id=1,
            original_url="https://delete.example.com",
            short_code="delete123",
            is_active=True,
            owner_id=owner_id
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_link
        mock_db.execute.return_value = mock_result
        
        user = MagicMock(spec=User)
        user.id = owner_id
        
        result = await link_service.delete_link("delete123", user)
        
        assert result is True
        mock_db.delete.assert_called_with(existing_link)
    
    @pytest.mark.asyncio
    async def test_delete_link_with_custom_alias(self, link_service, mock_db, mock_cache):
        """Test deleting link with custom alias deletes both from cache."""
        owner_id = uuid.uuid4()
        existing_link = Link(
            id=1,
            original_url="https://delete.example.com",
            short_code="delete123",
            custom_alias="my-alias",
            is_active=True,
            owner_id=owner_id
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_link
        mock_db.execute.return_value = mock_result
        
        user = MagicMock(spec=User)
        user.id = owner_id
        
        result = await link_service.delete_link("delete123", user)
        
        assert result is True
        # Should delete both short_code and custom_alias from cache
        assert mock_cache.delete_link.call_count == 2
    
    @pytest.mark.asyncio
    async def test_delete_link_not_found(self, link_service, mock_db, mock_cache):
        """Test deleting non-existent link returns False."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        
        result = await link_service.delete_link("nonexistent", user)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_link_not_owner(self, link_service, mock_db, mock_cache):
        """Test deleting link by non-owner raises PermissionError."""
        owner_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        
        existing_link = Link(
            id=1,
            original_url="https://delete.example.com",
            short_code="delete123",
            is_active=True,
            owner_id=owner_id
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_link
        mock_db.execute.return_value = mock_result
        
        user = MagicMock(spec=User)
        user.id = other_user_id  # Different from owner
        
        with pytest.raises(PermissionError):
            await link_service.delete_link("delete123", user)


class TestLinkServiceStats:
    """Tests for getting link statistics."""
    
    @pytest.mark.asyncio
    async def test_get_link_stats(self, link_service, mock_db, mock_cache):
        """Test getting link statistics."""
        link = Link(
            id=1,
            original_url="https://stats.example.com",
            short_code="stats123",
            click_count=42,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = link
        mock_db.execute.return_value = mock_result
        
        stats = await link_service.get_link_stats("stats123")
        
        assert stats == link
        assert stats.click_count == 42


class TestLinkServiceSearch:
    """Tests for searching links."""
    
    @pytest.mark.asyncio
    async def test_search_by_original_url(self, link_service, mock_db):
        """Test searching link by original URL."""
        expected_links = [Link(
            id=1,
            original_url="https://search.example.com",
            short_code="search123",
            is_active=True
        )]
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = expected_links
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result
        
        links = await link_service.search_by_original_url("https://search.example.com")
        
        assert links == expected_links


class TestLinkServiceCleanup:
    """Tests for cleanup operations."""
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_links(self, link_service, mock_db):
        """Test cleaning up expired links."""
        mock_result = MagicMock()
        mock_result.rowcount = 5
        mock_db.execute.return_value = mock_result
        
        deleted = await link_service.cleanup_expired_links()
        
        assert deleted == 5
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_cleanup_unused_links(self, link_service, mock_db):
        """Test cleaning up unused links."""
        mock_result = MagicMock()
        mock_result.rowcount = 3
        mock_db.execute.return_value = mock_result
        
        deleted = await link_service.cleanup_unused_links(days=30)
        
        assert deleted == 3
        mock_db.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_expired_links_history(self, link_service, mock_db):
        """Test getting expired links history."""
        expired_links = [
            Link(id=1, original_url="https://expired1.com", short_code="exp1", is_active=True),
            Link(id=2, original_url="https://expired2.com", short_code="exp2", is_active=True)
        ]
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = expired_links
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result
        
        links = await link_service.get_expired_links_history()
        
        assert links == expired_links


class TestLinkServiceUserLinks:
    """Tests for user links operations."""
    
    @pytest.mark.asyncio
    async def test_get_user_links(self, link_service, mock_db):
        """Test getting all links for a user."""
        user = MagicMock(spec=User)
        user.id = uuid.uuid4()
        
        user_links = [
            Link(id=1, original_url="https://user1.com", short_code="usr1", owner_id=user.id, is_active=True),
            Link(id=2, original_url="https://user2.com", short_code="usr2", owner_id=user.id, is_active=True)
        ]
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = user_links
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result
        
        links = await link_service.get_user_links(user)
        
        assert links == user_links


class TestLinkServiceProject:
    """Tests for project-related operations."""
    
    @pytest.mark.asyncio
    async def test_get_links_by_project(self, link_service, mock_db):
        """Test getting links by project."""
        project_links = [
            Link(id=1, original_url="https://proj1.com", short_code="prj1", project="myproject", is_active=True)
        ]
        
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = project_links
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result
        
        links = await link_service.get_links_by_project("myproject")
        
        assert links == project_links
