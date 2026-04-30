"""
Main FastAPI application entry point for BEYOND.
"""

from fastapi import FastAPI

app = FastAPI(title="BEYOND")


@app.get("/")
def read_root():
    return {"message": "BEYOND is alive"}
