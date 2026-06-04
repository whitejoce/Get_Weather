class WeatherError(Exception):
    """Base exception for weather query failures."""


class InvalidCityNameError(WeatherError):
    """Raised when a city name fails validation."""


class CityNotFoundError(WeatherError):
    """Raised when a city cannot be resolved to a weather area id."""


class NetworkError(WeatherError):
    """Raised when an upstream weather request fails."""


class ParseError(WeatherError):
    """Raised when upstream weather data cannot be parsed."""
