from fastapi import Request

from .services.alarm_service import AlarmService


def get_alarm_service(request: Request) -> AlarmService:
    return request.app.state.alarm_service
