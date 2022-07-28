import enum
import importlib.metadata


VERSION: str = importlib.metadata.version("lyjournal_scraper")


class OutputFormat(enum.Enum):
    CSV: enum.Enum = "csv"
    JSON: enum.Enum = "json"
