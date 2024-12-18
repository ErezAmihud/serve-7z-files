import anyio.to_thread
import uvicorn

from fastapi import FastAPI, Response
from pydantic_settings import BaseSettings, SettingsConfigDict
import py7zr

class Settings(BaseSettings):
    app_name: str = "Awesome API"
    zip_file: str = "README.7z"
    path_prefix: str|None = None
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
app = FastAPI()

index_page = r"""Hello!
This is the symbol server. The sources for getting new symbols can be found at ErezAmihud/WindowsSymbolsByVersion github repo.
This server is a basic serv of zip file because symbols weigh *a lot* when they are uncompressed."""

@app.get("/")
async def root():
    return Response(index_page, media_type="text")

def get_file_data(path):
    with py7zr.SevenZipFile(settings.zip_file, mode="r") as file_zip:
        return list(file_zip.read([path]).values())[0].read() # type: ignore


@app.get("/{pdbname}/{idname}/{pdbname2}")
async def get_symbol(pdbname, idname, pdbname2):
    path = f"{pdbname}/{idname}/{pdbname2}"
    if settings.path_prefix:
        path = f"{settings.path_prefix}/{path}"
    try:
        data = await anyio.to_thread.run_sync(get_file_data, path)
        return Response(data, media_type="application/octet-stream")
    except IndexError:
        return Response(status_code=404)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)