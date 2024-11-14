from server import app
from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)

