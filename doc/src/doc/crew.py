from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import BaseTool
from crewai.llm import LLM
from pydantic import BaseModel, Field
from typing import Type
from doc.src.doc.tools.Purchase_Tool import PurchaseOrderManager
from doc.src.doc.tools.Receipe_Tool import ReceiptManager
from doc.src.doc.tools.classification_manager import DocumentClassifier
from doc.src.doc.tools.Invoice_Tool import InvoiceManager
import os

# Initialize the document classifier with Azure credentials
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "your-api-key-here")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "your-endpoint-here")

# Create Azure LLM instance for agents
azure_llm = LLM(
    model="azure/gpt-4o",
    api_key=AZURE_API_KEY,
    api_base=AZURE_ENDPOINT,
    api_version="2024-12-01-preview"
)

classifier = DocumentClassifier(api_key=AZURE_API_KEY, endpoint=AZURE_ENDPOINT)

# Initialize the invoice manager with Azure Document Intelligence and Gemini API credentials
AZURE_DI_ENDPOINT = os.getenv("AZURE_DI_ENDPOINT", "your-azure-di-endpoint-here")
AZURE_DI_KEY = os.getenv("AZURE_DI_KEY", "your-azure-di-key-here")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")

invoice_manager = InvoiceManager(
    azure_endpoint=AZURE_DI_ENDPOINT,
    azure_key=AZURE_DI_KEY,
    gemini_api_key=GEMINI_API_KEY
)

purchase_order_manager = PurchaseOrderManager(
    azure_endpoint=AZURE_DI_ENDPOINT,
    azure_key=AZURE_DI_KEY,
    gemini_api_key=GEMINI_API_KEY
)
receipt_manager = ReceiptManager(
    azure_endpoint=AZURE_DI_ENDPOINT,
    azure_key=AZURE_DI_KEY,
    gemini_api_key=GEMINI_API_KEY
)

# ============================================================================
# Tool Schemas - Define input validation for each tool
# ============================================================================

class ClassifyDocumentInput(BaseModel):
    """Input schema for document classification tool."""
    document_path: str = Field(..., description="Path to the document file (PDF, PNG, JPG, etc.)")

class ExtractInvoiceInput(BaseModel):
    """Input schema for invoice extraction tool."""
    file_path: str = Field(..., description="Path to the invoice file")

class ProcessInvoiceInput(BaseModel):
    """Input schema for invoice processing tool."""
    source: str = Field(..., description="URL or file path to invoice")
    is_url: bool = Field(default=False, description="True if source is URL, False if file path")

class ExtractReceiptInput(BaseModel):
    """Input schema for receipt extraction tool."""
    file_path: str = Field(..., description="Path to the receipt file")

class ProcessReceiptInput(BaseModel):
    """Input schema for receipt processing tool."""
    source: str = Field(..., description="URL or file path to receipt")
    is_url: bool = Field(default=False, description="True if source is URL, False if file path")

class ExtractPOInput(BaseModel):
    """Input schema for purchase order extraction tool."""
    file_path: str = Field(..., description="Path to the purchase order file")

class ProcessPOInput(BaseModel):
    """Input schema for purchase order processing tool."""
    source: str = Field(..., description="URL or file path to purchase order")
    is_url: bool = Field(default=False, description="True if source is URL, False if file path")

# ============================================================================
# Tool Classes - Proper BaseTool subclasses
# ============================================================================

class ClassifyDocumentTool(BaseTool):
    """Tool for classifying documents into invoice, receipt, or purchase order."""
    name: str = "Classify Document"
    description: str = "Classify a document into invoice, receipt, or purchase order using Azure OpenAI GPT-4o Vision"
    args_schema: Type[BaseModel] = ClassifyDocumentInput

    def _run(self, document_path: str) -> str:
        """Execute document classification."""
        result = classifier.classify_document(document_path)
        return result.model_dump_json()


class ExtractInvoiceTool(BaseTool):
    """Tool for extracting invoice data."""
    name: str = "Extract Invoice"
    description: str = "Extract invoice data from a document file using Azure Document Intelligence"
    args_schema: Type[BaseModel] = ExtractInvoiceInput

    def _run(self, file_path: str) -> str:
        """Execute invoice extraction."""
        result = invoice_manager.extract_from_file(file_path)
        if hasattr(result, 'model_dump_json'):
            return result.model_dump_json()
        return str(result)


class ProcessInvoiceTool(BaseTool):
    """Tool for processing invoices end-to-end."""
    name: str = "Process Invoice"
    description: str = "Complete invoice processing pipeline: extract, validate, and structure data"
    args_schema: Type[BaseModel] = ProcessInvoiceInput

    def _run(self, source: str, is_url: bool = False) -> str:
        """Execute invoice processing."""
        result = invoice_manager.process_invoice(source, is_url)
        if hasattr(result, 'model_dump_json'):
            return result.model_dump_json()
        return str(result)


class ExtractReceiptTool(BaseTool):
    """Tool for extracting receipt data."""
    name: str = "Extract Receipt"
    description: str = "Extract receipt data from a document file using Azure Document Intelligence"
    args_schema: Type[BaseModel] = ExtractReceiptInput

    def _run(self, file_path: str) -> str:
        """Execute receipt extraction."""
        result = receipt_manager.extract_from_file(file_path)
        if hasattr(result, 'model_dump_json'):
            return result.model_dump_json()
        return str(result)


class ProcessReceiptTool(BaseTool):
    """Tool for processing receipts end-to-end."""
    name: str = "Process Receipt"
    description: str = "Complete receipt processing pipeline: extract, validate, and structure data"
    args_schema: Type[BaseModel] = ProcessReceiptInput

    def _run(self, source: str, is_url: bool = False) -> str:
        """Execute receipt processing."""
        result = receipt_manager.process_receipt(source, is_url)
        if hasattr(result, 'model_dump_json'):
            return result.model_dump_json()
        return str(result)


class ExtractPOTool(BaseTool):
    """Tool for extracting purchase order data."""
    name: str = "Extract Purchase Order"
    description: str = "Extract purchase order data from a document file using Azure Document Intelligence"
    args_schema: Type[BaseModel] = ExtractPOInput

    def _run(self, file_path: str) -> str:
        """Execute purchase order extraction."""
        result = purchase_order_manager.extract_from_file(file_path)
        if hasattr(result, 'model_dump_json'):
            return result.model_dump_json()
        return str(result)


class ProcessPOTool(BaseTool):
    """Tool for processing purchase orders end-to-end."""
    name: str = "Process Purchase Order"
    description: str = "Complete purchase order processing pipeline: extract, validate, and structure data"
    args_schema: Type[BaseModel] = ProcessPOInput

    def _run(self, source: str, is_url: bool = False) -> str:
        """Execute purchase order processing."""
        result = purchase_order_manager.process_purchase_order(source, is_url)
        if hasattr(result, 'model_dump_json'):
            return result.model_dump_json()
        return str(result)

# ============================================================================
# Tool Instances
# ============================================================================

classify_document_tool = ClassifyDocumentTool()
extract_invoice_tool = ExtractInvoiceTool()
process_invoice_tool = ProcessInvoiceTool()
extract_receipt_tool = ExtractReceiptTool()
process_receipt_tool = ProcessReceiptTool()
extract_po_tool = ExtractPOTool()
process_po_tool = ProcessPOTool()

# Uncomment the following line to use an example of a custom tool
# from doc.tools.custom_tool import MyCustomTool

# Check our tools documentations for more information on how to use them
# from crewai_tools import SerperDevTool

@CrewBase
class DocCrew():
	"""Doc crew"""
	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def manager(self) -> Agent:
		return Agent(
			config=self.agents_config['Document_Processing_Manager'],
			llm=azure_llm,
			verbose=False,
			tools=[classify_document_tool],
		)

	@agent
	def processing_invoice(self) -> Agent:
		return Agent(
			config=self.agents_config['processing_invoice'],
			llm=azure_llm,
			verbose=False,
			tools=[
				extract_invoice_tool,
				process_invoice_tool,
			],
		)
	@agent
	def processing_receipt(self) -> Agent:
		return Agent(
			config=self.agents_config['processing_receipt'],
			llm=azure_llm,
			verbose=False,
			tools=[
				extract_receipt_tool,
				process_receipt_tool,
			],
		)
	@agent
	def processing_purchase_order(self) -> Agent:
		return Agent(
			config=self.agents_config['purchase_order_agent'],
			llm=azure_llm,
			verbose=False,
			tools=[
				extract_po_tool,
				process_po_tool,
			],
		)

	
	@task
	def classification_task(self) -> Task:
		return Task(
			config=self.tasks_config['classification_task'],
			agent=self.manager(),
			
		)
	
	@task
	def invoice_processing_task(self) -> Task:
		return Task(
			config=self.tasks_config['invoice_processing_task'],
			agent=self.processing_invoice(),
			context=[self.classification_task()],
		)
	
	@task
	def receipt_processing_task(self) -> Task:
		return Task(
			config=self.tasks_config['receipt_processing_task'],
			agent=self.processing_receipt(),
			context=[self.classification_task()],
		)
	
	@task
	def purchase_order_processing_task(self) -> Task:
		return Task(
			config=self.tasks_config['purchase_order_processing_task'],
			agent=self.processing_purchase_order(),
			context=[self.classification_task()],
		)
    

	
	@crew
	def crew(self) -> Crew:
		"""Creates the Doc crew with sequential task routing"""
		# Sequential process executes tasks in order:
		# 1. classification_task → Manager classifies document
		# 2. invoice_processing_task → Invoice agent processes (or skips if not invoice)
		# 3. receipt_processing_task → Receipt agent processes (or skips if not receipt)
		# 4. purchase_order_processing_task → PO agent processes (or skips if not PO)
		#
		# Each specialist agent checks the classification result and only processes
		# if the document type matches their specialty.
		
		# Explicitly define task order to ensure correct execution sequence
		tasks_in_order = [
			self.classification_task(),
			self.invoice_processing_task(),
			self.receipt_processing_task(),
			self.purchase_order_processing_task(),
		]
		
		return Crew(
			agents=self.agents,  # All agents including manager
			tasks=tasks_in_order,   # Tasks in explicit order
			process=Process.sequential,  # Execute tasks in order
			verbose=False,
		)