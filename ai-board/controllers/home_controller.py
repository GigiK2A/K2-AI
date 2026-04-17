"""Home controller — thin FastAPI adapter on top of `HomeService`."""

from __future__ import annotations

from fastapi import APIRouter, Request

from interfaces.dashboard.routes import base_context, render
from services import HomeService

router = APIRouter()
_service = HomeService()


@router.get("/")
async def home_page(request: Request):
    data = _service.load_home_data()
    context = base_context(
        request,
        active_page="home",
        page_title="Panoramica",
        page_subtitle=data["today_label"],
    )
    context.update(data)
    return render(request, "home.html", context)


@router.get("/partials/kpi")
async def home_kpi_partial(request: Request):
    data = _service.load_home_data()
    context = base_context(request, active_page="home", page_title="Panoramica")
    context.update(data)
    return render(request, "partials/kpi_cards.html", context)


@router.get("/partials/activity")
async def home_activity_partial(request: Request):
    data = _service.load_home_data()
    context = base_context(request, active_page="home", page_title="Panoramica")
    context.update(data)
    return render(request, "partials/activity_feed.html", context)
