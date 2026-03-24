from fastapi import FastAPI
from routers.userflow import router as user_flow_router
from routers.datasets import router as datasets_router
from routers.training import router as training_router
import models.user_flow
import models.datasets
import models.trained_models
import models.training_data
from database import engine

app = FastAPI()

models.user_flow.Base.metadata.create_all(bind=engine)
models.datasets.Base.metadata.create_all(bind=engine)
models.trained_models.Base.metadata.create_all(bind=engine)
models.training_data.Base.metadata.create_all(bind=engine)

app.include_router(user_flow_router)
app.include_router(datasets_router)
app.include_router(training_router)