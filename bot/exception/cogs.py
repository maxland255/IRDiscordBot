class CogInitializationError(Exception):
    """Base exception for all cogs Error"""
    pass


class CriticalCogInitializationError(CogInitializationError):
    """Critical error, after that, the bot it's not available to work correctly."""
    pass


class NonCriticalCogInitializationError(CogInitializationError):
    """Non-critical error, after that, the bot it's available to work correctly or partially."""
    pass
