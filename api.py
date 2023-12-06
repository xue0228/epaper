import os
import shutil
from enum import Enum
from typing import Iterable

import uvicorn
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from constants import ROOT_DIR, HOST, API_PORT
from mode import BaseMode
from response import BaseResponse
from singleton import config, fixed_mode, movie_mode


def create_app(modes: Iterable[BaseMode]):
    mode_dict = {}
    for mode in modes:
        mode_dict[mode.name] = mode.name
    ModeName = Enum("ModeName", mode_dict)

    tags_metadata = [
        {
            "name": "fixed",
            "description": "固定画面模式",
        },
        {
            "name": "movie",
            "description": "慢放电影模式",
        },
    ]

    app = FastAPI(
        title="墨水屏控制",
        openapi_tags=tags_metadata,
    )

    @app.get("/mode/{mode_name}")
    def change_mode(mode_name: ModeName) -> BaseResponse:
        config.update_config({"base": {"mode": mode_name.value}})
        return BaseResponse(msg=f"mode changed:{mode_name.value}")

    @app.post("/mode/fixed/image", tags=["fixed"])
    def upload_fixed_image(file: UploadFile = File(...)) -> BaseResponse:
        with fixed_mode.lock:
            if "image" not in file.content_type:
                return BaseResponse(code=400, msg="image file only")
            fixed_mode.api_func(file.file)
            return BaseResponse(msg="image uploaded")

    class FixedItem(BaseModel):
        text: str
        alpha: float = 1

    @app.post("/mode/fixed/text", tags=["fixed"])
    def upload_fixed_text(item: FixedItem):
        with fixed_mode.lock:
            fixed_mode.api_func(None, item.text, item.alpha)
            return BaseResponse(msg="text uploaded")

    @app.post("/mode/movie/video", tags=["movie"])
    def upload_movie(file: UploadFile = File(...)) -> BaseResponse:
        with movie_mode.lock:
            if file.content_type != "video/mp4":
                return BaseResponse(code=400, msg="mp4 only")

            try:
                path = os.path.join(ROOT_DIR, "data", "tem.mp4")
                with open(path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                if os.path.exists(movie_mode._movie_path):
                    os.remove(movie_mode._movie_path)
                os.rename(path, movie_mode._movie_path)
                config.update_config({"movie": {"index": 0}})
            finally:
                file.file.close()
            return BaseResponse(msg="video uploaded")

    class MovieItem(BaseModel):
        index: int
        interval: int

    @app.put("/mode/movie/config", tags=["movie"])
    def update_movie_config(item: MovieItem):
        with movie_mode.lock:
            config.update_config({"movie": {"index": item.index, "interval": item.interval}})
            return BaseResponse(msg="movie config updated")

    return app


def run_api(modes: Iterable[BaseMode]):
    app = create_app(modes)
    uvicorn.run(app, host=HOST, port=API_PORT)
