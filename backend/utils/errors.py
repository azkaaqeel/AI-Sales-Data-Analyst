class InsightGenerationError(Exception):
    """Base exception for insight generation errors."""
    pass

class InsightInputError(InsightGenerationError):
    """Raised when invalid input is provided."""
    pass

class InsightModelError(InsightGenerationError):
    """Raised when model initialization or inference fails."""
    pass
