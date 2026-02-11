# LLD Implementation Skeleton
# Replace class and method names with your component-specific design.


class Repository:
    """Data access layer."""
    def get(self, entity_id: str):
        raise NotImplementedError

    def save(self, entity) -> None:
        raise NotImplementedError


class Service:
    """Core business logic."""
    def __init__(self, repository: Repository):
        self.repository = repository

    def execute(self, request):
        raise NotImplementedError
