from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

import docker

from service.db import add_user_to_leaderboard, get_leaderboard
from service.constant import UPLOAD_FOLDER
from service.message import Message
from service.docker import container_halt, find_container, run_container_game

app = FastAPI()

client = docker.from_env()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/leaderboard")
async def leaderboard():
    result = get_leaderboard()
    data = result.data
    leaderboard = [{ "time": row["created_at"], "name": row["name"], "score": row["score"]} for row in data]
    return JSONResponse({"leaderboard": leaderboard}, status_code=200)


@app.post("/upload-files/{name}")
async def upload_files(
    name: str,
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
):

    filenames = {file1.filename, file2.filename}
    if "maker.py" not in filenames or "requirements.txt" not in filenames:
        return JSONResponse({"error": "Incorrect files"}, status_code=404)

    upload_path = UPLOAD_FOLDER / name
    upload_path.mkdir(parents=True, exist_ok=True)

    for uploaded_file in [file1, file2]:
        with open(UPLOAD_FOLDER / name / uploaded_file.filename, "wb") as f:
            f.write(await uploaded_file.read())

    try:
        out = run_container_game(name)
        if isinstance(out, JSONResponse):
            return out

        add_user_to_leaderboard(name, out)
        return JSONResponse({"message": "Files uploaded successfully"}, status_code=200)


    except Exception as e:
        container = find_container(name)
        container_halt(container)
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        container = find_container(name)
        container_halt(container)