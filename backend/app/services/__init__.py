"""EVT-CLIP application services.

Keep this package initializer intentionally lightweight. Production inference
imports `app.services.evtclip_worker` inside a dedicated Modal CPU image that
does not install the web/database dependency stack. Eagerly importing every
service here would couple inference startup to SQLAlchemy/FastAPI and can break
the worker before model loading.

Import concrete services from their modules, for example:
`from app.services.report_service import ReportService`.
"""

__all__: list[str] = []
