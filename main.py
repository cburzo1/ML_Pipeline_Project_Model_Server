from fastapi import FastAPI
from routers.userflow import router as user_flow_router
import models.user_flow
from database import engine

app = FastAPI()

models.user_flow.Base.metadata.create_all(bind=engine)

app.include_router(user_flow_router)