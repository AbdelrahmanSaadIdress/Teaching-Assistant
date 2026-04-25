from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

class DoclingConverter:
    def __init__(self, do_ocr=True):
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = do_ocr

        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
    def convert_file(self, file_path: str):
        """
        Convert a document into structured Docling output.
        """
        result = self.converter.convert(file_path)
        document = result.document

        return document

    def to_markdown(self, document):
        return document.export_to_markdown()

    def to_text(self, document):
        return document.export_to_text()

    def to_dict(self, document):
        return document.export_to_dict()
    
