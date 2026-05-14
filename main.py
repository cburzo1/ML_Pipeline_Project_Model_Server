from fastapi import FastAPI
from routers.userflow import router as user_flow_router
from routers.datasets import router as datasets_router
from routers.training import router as training_router
from routers.predict import router as predict_router
from routers.metrics import router as metrics_router
import models.user_flow
import models.datasets
import models.trained_models
from database import engine

app = FastAPI()

models.user_flow.Base.metadata.create_all(bind=engine)
models.datasets.Base.metadata.create_all(bind=engine)
models.trained_models.Base.metadata.create_all(bind=engine)

app.include_router(user_flow_router)
app.include_router(datasets_router)
app.include_router(training_router)
app.include_router(predict_router)
app.include_router(metrics_router)