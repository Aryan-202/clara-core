from fastapi import FastAPI
from .api.ws.router import router as ws_router

clara = FastAPI()
clara.include_router(ws_router)


@clara.get("/")
async def root():
    return {
        "msg" : "clara backend is running"
    }


def main():
    """This is the entry point of clara-core """
    import uvicorn
    uvicorn.run("clara.main:clara", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
