"""Functional tests for links API."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
class TestCreateLink:
    """Tests for link creation endpoint."""
    
    async def test_create_link_anonymous(self, client: AsyncClient):
        """Test creating link without authentication."""
        response = await client.post(
            "/links/shorten",
            json={"original_url": "https://example.com/long-url-path"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["original_url"] == "https://example.com/long-url-path"
        assert "short_code" in data
        assert "short_url" in data
        assert data["owner_id"] is None
    
    async def test_create_link_authenticated(
        self, client: AsyncClient, auth_headers
    ):
        """Test creating link with authentication."""
        response = await client.post(
            "/links/shorten",
            headers=auth_headers,
            json={"original_url": "https://example.com/authenticated-url"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["original_url"] == "https://example.com/authenticated-url"
        assert data["owner_id"] is not None
    
    async def test_create_link_with_custom_alias(
        self, client: AsyncClient, auth_headers
    ):
        """Test creating link with custom alias."""
        response = await client.post(
            "/links/shorten",
            headers=auth_headers,
            json={
                "original_url": "https://example.com/custom",
                "custom_alias": "my-custom-link"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["custom_alias"] == "my-custom-link"
        assert "my-custom-link" in data["short_url"]
    
    async def test_create_link_with_expiry(
        self, client: AsyncClient, auth_headers
    ):
        """Test creating link with expiration."""
        expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        response = await client.post(
            "/links/shorten",
            headers=auth_headers,
            json={
                "original_url": "https://example.com/expiring",
                "expires_at": expires_at
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["expires_at"] is not None
    
    async def test_create_link_with_project(
        self, client: AsyncClient, auth_headers
    ):
        """Test creating link with project."""
        response = await client.post(
            "/links/shorten",
            headers=auth_headers,
            json={
                "original_url": "https://example.com/project",
                "project": "my-project"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["project"] == "my-project"
    
    async def test_create_link_invalid_url(self, client: AsyncClient):
        """Test creating link with invalid URL."""
        response = await client.post(
            "/links/shorten",
            json={"original_url": "invalid-url"}
        )
        
        assert response.status_code == 422
    
    async def test_create_link_duplicate_alias(
        self, client: AsyncClient, auth_headers, test_link_with_alias
    ):
        """Test creating link with duplicate alias."""
        response = await client.post(
            "/links/shorten",
            headers=auth_headers,
            json={
                "original_url": "https://example.com/new",
                "custom_alias": "my-custom-alias"  # Same as test_link_with_alias
            }
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
class TestGetLinkStats:
    """Tests for link statistics endpoint."""
    
    async def test_get_stats_success(
        self, client: AsyncClient, test_link
    ):
        """Test getting link statistics."""
        response = await client.get(f"/links/{test_link.short_code}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_url"] == test_link.original_url
        assert data["short_code"] == test_link.short_code
        assert "click_count" in data
        assert "created_at" in data
    
    async def test_get_stats_custom_alias(
        self, client: AsyncClient, test_link_with_alias
    ):
        """Test getting stats using custom alias."""
        response = await client.get(
            f"/links/{test_link_with_alias.custom_alias}/stats"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["custom_alias"] == test_link_with_alias.custom_alias
    
    async def test_get_stats_not_found(self, client: AsyncClient):
        """Test getting stats for non-existent link."""
        response = await client.get("/links/nonexistent/stats")
        
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateLink:
    """Tests for link update endpoint."""
    
    async def test_update_link_success(
        self, client: AsyncClient, auth_headers, test_link
    ):
        """Test updating link successfully."""
        response = await client.put(
            f"/links/{test_link.short_code}",
            headers=auth_headers,
            json={"original_url": "https://newurl.com/updated"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["original_url"] == "https://newurl.com/updated"
    
    async def test_update_link_unauthorized(
        self, client: AsyncClient, test_link
    ):
        """Test updating link without authentication."""
        response = await client.put(
            f"/links/{test_link.short_code}",
            json={"original_url": "https://newurl.com"}
        )
        
        assert response.status_code == 401
    
    async def test_update_link_not_owner(
        self, client: AsyncClient, anonymous_link, auth_headers
    ):
        """Test updating link by non-owner."""
        response = await client.put(
            f"/links/{anonymous_link.short_code}",
            headers=auth_headers,
            json={"original_url": "https://newurl.com"}
        )
        
        assert response.status_code == 403
    
    async def test_update_link_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Test updating non-existent link."""
        response = await client.put(
            "/links/nonexistent",
            headers=auth_headers,
            json={"original_url": "https://newurl.com"}
        )
        
        assert response.status_code == 404
    
    async def test_update_link_duplicate_alias(
        self, client: AsyncClient, auth_headers, test_link, test_link_with_alias
    ):
        """Test updating link with duplicate custom alias."""
        response = await client.put(
            f"/links/{test_link.short_code}",
            headers=auth_headers,
            json={"custom_alias": "my-custom-alias"}  # Already used by test_link_with_alias
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    async def test_update_link_custom_alias(
        self, client: AsyncClient, auth_headers, test_link
    ):
        """Test updating link custom alias."""
        response = await client.put(
            f"/links/{test_link.short_code}",
            headers=auth_headers,
            json={"custom_alias": "new-unique-alias"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["custom_alias"] == "new-unique-alias"
    
    async def test_update_link_expires_at(
        self, client: AsyncClient, auth_headers, test_link
    ):
        """Test updating link expiration."""
        from datetime import datetime, timedelta
        new_expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
        
        response = await client.put(
            f"/links/{test_link.short_code}",
            headers=auth_headers,
            json={"expires_at": new_expires}
        )
        
        assert response.status_code == 200
    
    async def test_update_link_project(
        self, client: AsyncClient, auth_headers, test_link
    ):
        """Test updating link project."""
        response = await client.put(
            f"/links/{test_link.short_code}",
            headers=auth_headers,
            json={"project": "new-project"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["project"] == "new-project"


@pytest.mark.asyncio
class TestDeleteLink:
    """Tests for link deletion endpoint."""
    
    async def test_delete_link_success(
        self, client: AsyncClient, auth_headers, test_link
    ):
        """Test deleting link successfully."""
        response = await client.delete(
            f"/links/{test_link.short_code}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
    
    async def test_delete_link_unauthorized(
        self, client: AsyncClient, test_link
    ):
        """Test deleting link without authentication."""
        response = await client.delete(f"/links/{test_link.short_code}")
        
        assert response.status_code == 401
    
    async def test_delete_link_not_owner(
        self, client: AsyncClient, anonymous_link, auth_headers
    ):
        """Test deleting link by non-owner."""
        response = await client.delete(
            f"/links/{anonymous_link.short_code}",
            headers=auth_headers
        )
        
        assert response.status_code == 403
    
    async def test_delete_link_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Test deleting non-existent link."""
        response = await client.delete(
            "/links/nonexistent",
            headers=auth_headers
        )
        
        assert response.status_code == 404


@pytest.mark.asyncio
class TestSearchLinks:
    """Tests for link search endpoint."""
    
    async def test_search_by_original_url(
        self, client: AsyncClient, test_link
    ):
        """Test searching by original URL."""
        response = await client.get(
            "/links/search",
            params={"original_url": test_link.original_url}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["links"]) >= 1
    
    async def test_search_no_results(self, client: AsyncClient):
        """Test search with no matching results."""
        response = await client.get(
            "/links/search",
            params={"original_url": "https://nonexistent.com/url"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["links"]) == 0


@pytest.mark.asyncio
class TestRedirect:
    """Tests for URL redirection endpoint."""
    
    async def test_redirect_success(
        self, client: AsyncClient, test_link
    ):
        """Test successful redirect."""
        response = await client.get(
            f"/{test_link.short_code}",
            follow_redirects=False
        )
        
        assert response.status_code == 307
        assert response.headers["location"] == test_link.original_url
    
    async def test_redirect_custom_alias(
        self, client: AsyncClient, test_link_with_alias
    ):
        """Test redirect using custom alias."""
        response = await client.get(
            f"/{test_link_with_alias.custom_alias}",
            follow_redirects=False
        )
        
        assert response.status_code == 307
        assert response.headers["location"] == test_link_with_alias.original_url
    
    async def test_redirect_not_found(self, client: AsyncClient):
        """Test redirect for non-existent link."""
        response = await client.get("/nonexistent123")
        
        assert response.status_code == 404
    
    async def test_redirect_expired_link(
        self, client: AsyncClient, expired_link
    ):
        """Test redirect for expired link."""
        response = await client.get(f"/{expired_link.short_code}")
        
        assert response.status_code == 404


@pytest.mark.asyncio
class TestUserLinks:
    """Tests for user links endpoints."""
    
    async def test_get_my_links(
        self, client: AsyncClient, auth_headers, test_link
    ):
        """Test getting user's links."""
        response = await client.get(
            "/links/user/my-links",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    async def test_get_my_links_unauthorized(self, client: AsyncClient):
        """Test getting links without authentication."""
        response = await client.get("/links/user/my-links")
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestAdminEndpoints:
    """Tests for admin cleanup endpoints."""
    
    async def test_cleanup_expired_links(
        self, client: AsyncClient, auth_headers
    ):
        """Test cleanup expired links endpoint."""
        response = await client.post(
            "/links/admin/cleanup/expired",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data
    
    async def test_cleanup_unused_links(
        self, client: AsyncClient, auth_headers
    ):
        """Test cleanup unused links endpoint."""
        response = await client.post(
            "/links/admin/cleanup/unused?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data
    
    async def test_get_expired_history(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting expired links history."""
        response = await client.get(
            "/links/admin/expired-history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    async def test_cleanup_unauthorized(self, client: AsyncClient):
        """Test cleanup endpoints require authentication."""
        response = await client.post("/links/admin/cleanup/expired")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestProjectLinks:
    """Tests for project-related link endpoints."""
    
    async def test_get_project_links(
        self, client: AsyncClient, auth_headers
    ):
        """Test getting links by project."""
        # First create a link with project
        await client.post(
            "/links/shorten",
            headers=auth_headers,
            json={
                "original_url": "https://example.com/project-link",
                "project": "test-project"
            }
        )
        
        response = await client.get(
            "/links/project/test-project",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    async def test_get_project_links_empty(self, client: AsyncClient):
        """Test getting links for empty project."""
        response = await client.get("/links/project/nonexistent-project")
        
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
class TestHealthAndRoot:
    """Tests for health and root endpoints."""
    
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
    
    async def test_health_endpoint(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
