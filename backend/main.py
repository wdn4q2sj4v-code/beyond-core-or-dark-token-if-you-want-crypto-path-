from fastapi import FastAPI

from errors import GovernanceBrainBlockError, governance_brain_block_handler
from routers.releases import router as releases_router

app = FastAPI()

app.add_exception_handler(GovernanceBrainBlockError, governance_brain_block_handler)
app.include_router(releases_router)


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}
