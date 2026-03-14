"""
Run with:
    locust -f tests/test_load/locustfile.py --host=http://localhost:8000

Or headless:
    locust -f tests/test_load/locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
"""

import random
import string
from locust import HttpUser, task, between, events


def random_url():
    """Генерирует случайный URL для тестирования."""
    path = ''.join(random.choices(string.ascii_lowercase, k=20))
    return f"https://example.com/{path}"


def random_alias():
    """Генерирует случайный псевдоним для тестирования."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


class URLShortenerUser(HttpUser):
    """Симулированный пользователь для нагрузочного тестирования сервиса."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Инициализация пользователя"""
        self.created_links = []
        self.token = None
        username = f"user_{random_alias()}"
        email = f"{username}@test.com"
        password = "testpassword123"
        response = self.client.post(
            "/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password
            }
        )
        
        if response.status_code == 201:
            response = self.client.post(
                "/auth/jwt/login",
                data={
                    "username": email,
                    "password": password
                }
            )
            if response.status_code == 200:
                self.token = response.json()["access_token"]
    
    @property
    def auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(10)
    def create_link(self):
        """создание короткой ссылки без псевдонима."""
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
        """создание ссылки с пользовательским псевдонимом."""
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
        """Доступ к сокращенной ссылке."""
        if self.created_links:
            code = random.choice(self.created_links)
            self.client.get(
                f"/{code}",
                allow_redirects=False,
                name="/[short_code]"
            )
    
    @task(10)
    def get_link_stats(self):
        """Получение статистики по ссылке."""
        if self.created_links:
            code = random.choice(self.created_links)
            self.client.get(
                f"/links/{code}/stats",
                name="/links/[short_code]/stats"
            )
    
    @task(3)
    def search_link(self):
        """Поиск ссылки по оригинальному URL."""
        url = random_url()
        self.client.get(
            "/links/search",
            params={"original_url": url}
        )
    
    @task(5)
    def get_my_links(self):
        """Получение ссылок пользователя."""
        self.client.get(
            "/links/user/my-links",
            headers=self.auth_headers
        )
    
    @task(2)
    def update_link(self):
        """Обновление оригинального URL для существующей ссылки."""
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
        """Удаление ссылки."""
        if self.created_links and self.token:
            code = self.created_links.pop(0)
            self.client.delete(
                f"/links/{code}",
                headers=self.auth_headers,
                name="/links/[short_code]"
            )
    
    @task(5)
    def health_check(self):
        self.client.get("/health")


class AnonymousUser(HttpUser):
    """Анонимный пользователь для тестирования доступа без аутентификации."""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        self.created_links = []
    
    @task(10)
    def create_anonymous_link(self):
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
        if self.created_links:
            code = random.choice(self.created_links)
            self.client.get(
                f"/{code}",
                allow_redirects=False,
                name="/[short_code]"
            )
    
    @task(5)
    def get_stats(self):
        if self.created_links:
            code = random.choice(self.created_links)
            self.client.get(
                f"/links/{code}/stats",
                name="/links/[short_code]/stats"
            )


class CacheTestUser(HttpUser):
    """Пользователь для тестирования кэширования при повторном доступе к одной и той же ссылке."""
    
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Создаем одну ссылку для тестирования кэширования."""
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
        """Доступ к одной и той же ссылке для проверки кэширования."""
        if self.short_code:
            self.client.get(
                f"/{self.short_code}",
                allow_redirects=False,
                name="/[short_code] (cached)"
            )


# Отчеты о начале и окончании теста
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
