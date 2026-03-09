"""
Locust load testing for URL Shortener API.

Run with:
    locust -f tests/test_load/locustfile.py --host=http://localhost:8000

Or headless:
    locust -f tests/test_load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
"""

import random
import string
from locust import HttpUser, task, between, events


def random_url():
    """Generate a random URL for testing."""
    path = ''.join(random.choices(string.ascii_lowercase, k=20))
    return f"https://example.com/{path}"


def random_alias():
    """Generate a random alias for testing."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


class URLShortenerUser(HttpUser):
    """Simulated user for load testing URL shortener."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Initialize user session."""
        self.created_links = []
        self.token = None
        
        # Register and login
        username = f"user_{random_alias()}"
        email = f"{username}@test.com"
        password = "testpassword123"
        
        # Register
        response = self.client.post(
            "/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password
            }
        )
        
        if response.status_code == 201:
            # Login (FastAPI Users uses /auth/jwt/login)
            response = self.client.post(
                "/auth/jwt/login",
                data={
                    "username": email,  # FastAPI Users uses email for auth
                    "password": password
                }
            )
            if response.status_code == 200:
                self.token = response.json()["access_token"]
    
    @property
    def auth_headers(self):
        """Get authorization headers."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(10)
    def create_link(self):
        """Create a shortened link."""
        url = random_url()
        response = self.client.post(
            "/links/shorten",
            headers=self.auth_headers,
            json={"original_url": url}
        )
        
        if response.status_code == 201:
            data = response.json()
            self.created_links.append(data["short_code"])
    
    @task(5)
    def create_link_with_alias(self):
        """Create a link with custom alias."""
        url = random_url()
        alias = random_alias()
        
        response = self.client.post(
            "/links/shorten",
            headers=self.auth_headers,
            json={
                "original_url": url,
                "custom_alias": alias
            }
        )
        
        if response.status_code == 201:
            self.created_links.append(alias)
    
    @task(20)
    def redirect_link(self):
        """Access a shortened link (redirect)."""
        if self.created_links:
            code = random.choice(self.created_links)
            self.client.get(
                f"/{code}",
                allow_redirects=False,
                name="/[short_code]"
            )
    
    @task(10)
    def get_link_stats(self):
        """Get statistics for a link."""
        if self.created_links:
            code = random.choice(self.created_links)
            self.client.get(
                f"/links/{code}/stats",
                name="/links/[short_code]/stats"
            )
    
    @task(3)
    def search_link(self):
        """Search for a link by original URL."""
        url = random_url()
        self.client.get(
            "/links/search",
            params={"original_url": url}
        )
    
    @task(5)
    def get_my_links(self):
        """Get user's links."""
        self.client.get(
            "/links/user/my-links",
            headers=self.auth_headers
        )
    
    @task(2)
    def update_link(self):
        """Update a link."""
        if self.created_links and self.token:
            code = random.choice(self.created_links)
            new_url = random_url()
            self.client.put(
                f"/links/{code}",
                headers=self.auth_headers,
                json={"original_url": new_url},
                name="/links/[short_code]"
            )
    
    @task(1)
    def delete_link(self):
        """Delete a link."""
        if self.created_links and self.token:
            code = self.created_links.pop(0)
            self.client.delete(
                f"/links/{code}",
                headers=self.auth_headers,
                name="/links/[short_code]"
            )
    
    @task(5)
    def health_check(self):
        """Check health endpoint."""
        self.client.get("/health")


class AnonymousUser(HttpUser):
    """Anonymous user without authentication."""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Initialize anonymous user."""
        self.created_links = []
    
    @task(10)
    def create_anonymous_link(self):
        """Create a link without authentication."""
        url = random_url()
        response = self.client.post(
            "/links/shorten",
            json={"original_url": url}
        )
        
        if response.status_code == 201:
            data = response.json()
            self.created_links.append(data["short_code"])
    
    @task(30)
    def redirect_link(self):
        """Access a shortened link."""
        if self.created_links:
            code = random.choice(self.created_links)
            self.client.get(
                f"/{code}",
                allow_redirects=False,
                name="/[short_code]"
            )
    
    @task(5)
    def get_stats(self):
        """Get link statistics."""
        if self.created_links:
            code = random.choice(self.created_links)
            self.client.get(
                f"/links/{code}/stats",
                name="/links/[short_code]/stats"
            )


class CacheTestUser(HttpUser):
    """User for testing cache performance."""
    
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Create a single link to test cache."""
        url = random_url()
        response = self.client.post(
            "/links/shorten",
            json={"original_url": url}
        )
        
        if response.status_code == 201:
            self.short_code = response.json()["short_code"]
        else:
            self.short_code = None
    
    @task
    def access_cached_link(self):
        """Repeatedly access the same link to test caching."""
        if self.short_code:
            self.client.get(
                f"/{self.short_code}",
                allow_redirects=False,
                name="/[short_code] (cached)"
            )


# Event hooks for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("Load test finished!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
