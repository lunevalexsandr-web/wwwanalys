from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, analysis_type, process_log, templates, reports, external
from app.core.database import engine, Base
from app.models import User, AnalysisType, Indicator, ProcessLog, IndicatorValue

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WWWAnalys API",
    description="API для учета производственных анализов",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(external.router, prefix="/api/external", tags=["External Integration"])
app.include_router(analysis_type.router, prefix="/analysis-types", tags=["Analysis Types"])
app.include_router(process_log.router, prefix="/process-logs", tags=["Process Logs"])

@app.get("/")
def read_root():
    return {"message": "Welcome to WWWAnalys API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}