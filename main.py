from fastapi import FastAPI
from routers.userflow import router as user_flow_router
from routers.datasets import router as datasets_router
import models.user_flow
import models.datasets
from database import engine

app = FastAPI()

models.user_flow.Base.metadata.create_all(bind=engine)
models.datasets.Base.metadata.create_all(bind=engine)

app.include_router(user_flow_router)
app.include_router(datasets_router)