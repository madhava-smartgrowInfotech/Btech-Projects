from fastapi import Request

from app.services.simulation_service import SimulationService


def get_service(request: Request) -> SimulationService:
    return request.app.state.service
