class GridFlexError(Exception):
    """Base class for all GridFlex domain errors."""


class InvalidConfiguration(GridFlexError):
    def __init__(self, message: str):
        super().__init__(message)


class GridNotFound(GridFlexError):
    def __init__(self, grid_id: str):
        self.grid_id = grid_id
        super().__init__(f"Grid '{grid_id}' was not found.")


class InvalidGrid(GridFlexError):
    def __init__(self, message: str, details: list[dict] | None = None):
        self.details = details or []
        super().__init__(message)


class PowerFlowDidNotConverge(GridFlexError):
    def __init__(
        self,
        message: str,
        max_mismatch: float | None = None,
        iterations: int | None = None,
    ):
        self.max_mismatch = max_mismatch
        self.iterations = iterations
        super().__init__(message)


class ScilabUnavailable(GridFlexError):
    def __init__(self, message: str):
        super().__init__(message)


class InvalidEngine(GridFlexError):
    def __init__(self, message: str):
        super().__init__(message)


class AnalysisNotFound(GridFlexError):
    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        super().__init__(f"Analysis '{analysis_id}' was not found.")
