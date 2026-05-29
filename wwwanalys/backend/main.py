from fastapi import FastAPI
from app.api import auth, analysis_type, process_log
from app.core.database import engine, Base
from app.models import User, AnalysisType, Indicator, ProcessLog, IndicatorValue

# Создаем таблицы в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="WWWAnalys API",
    description="API для учета производственных анализов",
    version="1.0.0"
)

# Подключаем роуты
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(analysis_type.router, prefix="/analysis-types", tags=["Analysis Types"])
app.include_router(process_log.router, prefix="/process-logs", tags=["Process Logs"])

@app.get("/")
def read_root():
    return {"message": "Welcome to WWWAnalys API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}