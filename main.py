from fastapi import FastAPI
app = FastAPI()


from routes import startRoute, dataRoute, QGRoute, SGRoute, QARoute

app.include_router(startRoute)
app.include_router(dataRoute)
app.include_router(QGRoute)
app.include_router(SGRoute)
app.include_router(QARoute)

# from helpers import get_settings, Settings, save_graph_png
# from stores.llm.LLMProviderFactory import LLMProviderFactory
# app_settings = get_settings()

# # model = LLMProviderFactory(app_settings).create(
# #         provider=app_settings.GENERATION_BACKEND,
# #         model_id=app_settings.GENERATION_MODEL_ID,
# #         model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE
# #     )

# # # model.invoke("What is 2+2?")
# # print(model.invoke("What is 2+2?"))

