from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, analysis_type, process_log, templates, reports, external, indicators, presets, statistics, plans
from app.core.database import engine, Base
from app.core.config import settings
from app.models import User, AnalysisType, Indicator, ProcessLog, IndicatorValue, Preset, PresetIndicator, AnalysisPlan, PlanItem
import uvicorn

# Создаем таблицы в базе данных
def ensure_indicator_columns(engine):
    with engine.connect() as conn:
        conn.execute(text(
            """
            ALTER TABLE indicators
            ADD COLUMN IF NOT EXISTS data_type VARCHAR DEFAULT 'number',
            ADD COLUMN IF NOT EXISTS options TEXT
            """
        ))
        conn.execute(text(
            """
            ALTER TABLE indicator_values
            ADD COLUMN IF NOT EXISTS text_value VARCHAR
            """
        ))
        conn.commit()

try:
    Base.metadata.create_all(bind=engine)
    ensure_indicator_columns(engine)
    print("Database tables created successfully")
except Exception as e:
    print(f"Error creating database tables: {e}")
    # Продолжаем запуск, даже если таблицы не создались (возможно, они уже существуют)

app = FastAPI(
    title="WWWAnalys API",
    description="API для учета производственных анализов",
    version="1.0.0"
)

# Настройка CORS из конфига
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
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
app.include_router(indicators.router, prefix="/api/indicators", tags=["Indicator Library"])
app.include_router(presets.router, prefix="/api/presets", tags=["Presets"])
app.include_router(statistics.router, prefix="/api", tags=["Statistics"])
app.include_router(plans.router, prefix="/api/plans", tags=["Plans"])

@app.get("/")
def read_root():
    return {"message": "Welcome to WWWAnalys API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)