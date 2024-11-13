from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

import docker
import tarfile
import uuid
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client = docker.from_env()

UPLOAD_FOLDER = Path("uploads")
MM_ENV_FOLDER = Path("MM-game-skeleton")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

def create_tar_archive(src_path: Path, arcname: str):
    tar_path = src_path.with_suffix(".tar")
    with tarfile.open(tar_path, "w") as tar:
        tar.add(src_path, arcname=arcname)
    return tar_path

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/container-list")
async def container_list():
    containers = client.containers.list(all=True)
    return [c.name for c in containers]

@app.post("/upload-files")
async def upload_files(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
):

    filenames = {file1.filename, file2.filename}
    if "maker.py" not in filenames or "requirements.txt" not in filenames:
        return JSONResponse({"error": "Incorrect files"}, status_code=404)

    for uploaded_file in [file1, file2]:
        with open(UPLOAD_FOLDER / uploaded_file.filename, "wb") as f:
            f.write(await uploaded_file.read())

    try:
        container_name = f"mm-env-container-{uuid.uuid4()}"
        if not client.images.list(name="mm-game:latest"):
            print("Building image")
            client.images.pull("kipiiler75/mm-game")
        container = client.containers.run(
            "kipiiler75/mm-game",
            detach=True,
            tty=True,
            name=container_name
        )

        src_maker = UPLOAD_FOLDER / "maker.py"
        maker_tar = create_tar_archive(src_maker, 'maker.py')
        with open(maker_tar, 'rb') as tar:
            container.put_archive('/app', tar.read())

        src_requirements = UPLOAD_FOLDER / "requirements.txt"
        req_tar = create_tar_archive(src_requirements, 'requirements.txt')
        with open(req_tar, 'rb') as tar:
            container.put_archive('/app', tar.read())

        exit_code, output = container.exec_run("pip install -r /app/requirements.txt")
        if exit_code != 0:
            container.stop()
            container.remove()
            return JSONResponse({"error": "Failed to install dependencies", "details": output.decode()}, status_code=500)
        
        for i in range(10):
            exit_code, output = container.exec_run("python /app/main.py -f")
            if exit_code != 0:
                container.stop()
                container.remove()
                return JSONResponse({"error": f"Failed during main.py execution on iteration {i+1}", "details": output.decode()}, status_code=500)


        exit_code, file_paths_output = container.exec_run("ls /app/log")
        file_names = file_paths_output.decode().splitlines()
        score = 0
        for f in file_names:
            score += int(f.split("_")[1].split(".")[0])
        print(f"Score: {score/len(file_names)}")
        score /= len(file_names)


    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        try:
            container.stop()
            container.remove()
        except:
            pass

    return JSONResponse({"status": "Files processed and container executed successfully", "result": score}, status_code=200)
