from fastapi import FastAPI
from routers.userflow import router as user_flow_router
import models.user_flow
from database import engine

app = FastAPI()

# Create the tables
models.user_flow.Base.metadata.create_all(bind=engine)

# Register router
app.include_router(user_flow_router)