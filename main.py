from fastapi import FastAPI
app = FastAPI()


from routes import startRoute, dataRoute, QGRoute, SGRoute, QARoute, BulkQGRoute

app.include_router(startRoute)
app.include_router(dataRoute)
app.include_router(QGRoute)
app.include_router(SGRoute)
app.include_router(QARoute)
app.include_router(BulkQGRoute)


# # # from helpers import get_settings, Settings, save_graph_png
# # # from stores.llm.LLMProviderFactory import LLMProviderFactory
# # # app_settings = get_settings()

# # # # model = LLMProviderFactory(app_settings).create(
# # # #         provider=app_settings.GENERATION_BACKEND,
# # # #         model_id=app_settings.GENERATION_MODEL_ID,
# # # #         model_temperature=app_settings.GENERATION_DAFAULT_TEMPERATURE
# # # #     )

# # # # # model.invoke("What is 2+2?")
# # # # print(model.invoke("What is 2+2?"))

# # from models.QuestionGeneration.QGGraphs import QG_Graph
# # from models.SummarizationGeneration.SGGraphs import SG_Graph
# # from models.QuestionAnswering.QAGraphs import QA_Graph

# # QA_Graph.get_graph().draw_mermaid_png(output_file_path="qa_graph.png")
# # QG_Graph.get_graph().draw_mermaid_png(output_file_path="qg_graph.png")
# # SG_Graph.get_graph().draw_mermaid_png(output_file_path="sg_graph.png")

