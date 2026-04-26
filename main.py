from fastapi import FastAPI
app = FastAPI()


from routes import startRoute, dataRoute, QGRoute, SGRoute, QARoute, BulkQGRoute

app.include_router(startRoute)
app.include_router(dataRoute)
app.include_router(QGRoute)
app.include_router(SGRoute)
app.include_router(QARoute)
app.include_router(BulkQGRoute)


from models.QuestionGeneration.QGGraphs import QG_Graph
from models.SummarizationGeneration.SGGraphs import SG_Graph
from models.QuestionAnswering.QAGraphs import QA_Graph
from models.ExamsGeneration.BulkGraph import BulkQG_Graph

QA_Graph.get_graph().draw_mermaid_png(output_file_path="qa_graph.png")
QG_Graph.get_graph().draw_mermaid_png(output_file_path="qg_graph.png")
SG_Graph.get_graph().draw_mermaid_png(output_file_path="sg_graph.png")
BulkQG_Graph.get_graph().draw_mermaid_png(output_file_path="exams_graph.png")
