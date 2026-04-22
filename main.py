from fastapi import FastAPI
app = FastAPI()


from routes import startRoute, dataRoute, QGRoute, SGRoute, QARoute

app.include_router(startRoute)
app.include_router(dataRoute)
app.include_router(QGRoute)
app.include_router(SGRoute)
app.include_router(QARoute)
