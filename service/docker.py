from pathlib import Path
import docker
import tarfile

from service.constant import UPLOAD_FOLDER
from service.message import Message, INTERNAL_SERVER_ERROR, BAD_REQUEST, NOT_FOUND, OK
import re

docker_client = docker.from_env()

def create_tar_archive(src_path, arcname):
    tar_path = src_path.with_suffix(".tar")
    with tarfile.open(tar_path, "w") as tar:
        tar.add(src_path, arcname=arcname)
    return tar_path

def prepare_container(container: docker.models.containers.Container, name: str):
    src_maker = UPLOAD_FOLDER / name / "maker.py"
    maker_tar = create_tar_archive(src_maker, 'maker.py')
    with open(maker_tar, 'rb') as tar:
        container.put_archive('/app', tar.read())
    
    src_requirements = UPLOAD_FOLDER / name / "requirements.txt"
    req_tar = create_tar_archive(src_requirements, 'requirements.txt')
    with open(req_tar, 'rb') as tar:
        container.put_archive('/app', tar.read())

def container_halt(container: docker.models.containers.Container):
    if container == None:
        return
    container.stop()
    container.remove()

def find_container(name: str):
    container_name = f"mm-env-container-{name}"
    try:
        container = docker_client.containers.get(container_name)
    except docker.errors.NotFound:
        return None
    return container

def run_container_game(name: str):
    container_name = f"mm-env-container-{name}"
    container = docker_client.containers.run(
        "kipiiler75/mm-game",
        detach=True,
        tty=True,
        name=container_name
    )

    prepare_container(container, name)

    exit_code, output = container.exec_run("pip install -r /app/requirements.txt")
    if exit_code != 0:
        container_halt(container)
        return Message("Failed to install requirements", error=True, detail=output.decode(), status=INTERNAL_SERVER_ERROR).json()
    
    exit_code, output = container.exec_run("python /app/admin_run.py")
    if exit_code != 0:
        container_halt(container)
        return Message("Failed to run simulation", error=True, detail=output.decode(), status=INTERNAL_SERVER_ERROR).json()
    
    output_str = output.decode()
    match = re.search(r"Average profit: ([\-\d\.]+)", output_str)
    if match:
        average_profit = float(match.group(1))
        container_halt(container)
        return average_profit
    else:
        container_halt(container)
        return Message("Average profit not found", error=True, detail=output_str, status=BAD_REQUEST).json()
