"""Custom exception classes for LeadMe."""

from fastapi import HTTPException, status


class RouteNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")


class AssignmentNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")


class ScheduleNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found")


class OutsideMumbaiError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coordinates are outside Mumbai service area",
        )


class RouteAlreadyActiveError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active route assignment",
        )
