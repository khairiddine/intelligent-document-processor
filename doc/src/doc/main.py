#!/usr/bin/env python
"""
Document Processing Application
Orchestrates the classification and processing of invoices, receipts, and purchase orders.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Add the current directory to Python path to allow imports
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# PHOENIX TRACING SETUP - Register only once to avoid blocking
# ============================================================================

from phoenix.otel import register

tracer_provider = register(
        project_name="document-processing-system",
        endpoint="https://app.phoenix.arize.com/s/khairibou20/v1/traces",
        auto_instrument=True
    )
    
  
# Import crew AFTER Phoenix is configured
from crew import DocCrew

def validate_document_path(document_path: str) -> bool:
    """
    Validate that the document file exists.
    
    Args:
        document_path: Path to the document file
        
    Returns:
        bool: True if file exists, False otherwise
    """
    if not Path(document_path).exists():
        print(f"[ERROR] Error: Document file not found at {document_path}")
        return False
    
    # Check file extension
    valid_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif'}
    file_ext = Path(document_path).suffix.lower()
    if file_ext not in valid_extensions:
        print(f"[ERROR] Error: Unsupported file format '{file_ext}'. Supported: {valid_extensions}")
        return False
    
    return True


def validate_environment_variables() -> bool:
    """
    Validate that all required environment variables are set.
    
    Returns:
        bool: True if all variables are set, False otherwise
    """
    required_vars = {
        'AZURE_OPENAI_API_KEY': 'Azure OpenAI API Key for classification and data mapping',
        'AZURE_OPENAI_ENDPOINT': 'Azure OpenAI Endpoint',
        'AZURE_DI_ENDPOINT': 'Azure Document Intelligence Endpoint',
        'AZURE_DI_KEY': 'Azure Document Intelligence API Key'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  • {var}: {description}")
    
    if missing_vars:
        print("[ERROR] Error: Missing required environment variables:")
        for var in missing_vars:
            print(var)
        print("\nSet them using:")
        print("  $env:VARIABLE_NAME = 'value'  # PowerShell")
        print("  export VARIABLE_NAME='value'  # Bash/Linux")
        return False
    
    return True


def run(document_path: str = None):
    """
    Main entry point for the document processing application.
    
    Args:
        document_path: Path to the document file to process.
                      If not provided, user will be prompted to enter it.
    
    Workflow:
        1. Validate environment variables
        2. Get document path from user if not provided
        3. Validate document file exists
        4. Initialize the crew
        5. Run the hierarchical document processing:
           - Manager classifies the document
           - Manager delegates to appropriate specialist:
             * Invoice agent for invoices
             * Receipt agent for receipts
             * Purchase order agent for POs
    """
    print("\n" + "="*60)
    print("[*] Document Processing System")
    print("="*60)
    
    # Step 1: Validate environment variables
    print("\n[*] Validating configuration...")
    if not validate_environment_variables():
        print("\n[!] Please set the required environment variables and try again.")
        return
    print("[OK] Configuration validated")
    
    # Step 2: Get document path
    if document_path is None:
        print("\n[*] Enter the path to your document (PDF, PNG, JPG, etc.):")
        document_path = input("  Document path: ").strip()
    
    # Step 3: Validate document file
    print(f"\n[*] Processing document: {document_path}")
    if not validate_document_path(document_path):
        return
    print("[OK] Document validated")
    
    # Step 4: Initialize the crew
    print("\n[*] Initializing document processing crew...")
    crew = DocCrew()
    
    # Step 5: Prepare inputs for the crew
    inputs = {
        'document_path': document_path
    }
    
    # Step 6: Run the crew with hierarchical process
    print("\n[*] Starting document processing workflow...")
    print("-" * 60)
    print("Step 1: Classification Phase")
    print("        Manager will classify the document type")
    print("-" * 60)
    
    try:
        # Add trace annotations for monitoring
        from opentelemetry import trace
        current_span = trace.get_current_span()
        
        # Annotate with document info
        current_span.set_attribute("document.path", document_path)
        current_span.set_attribute("document.name", Path(document_path).name)
        current_span.set_attribute("document.size_bytes", Path(document_path).stat().st_size)
        
        # Run the crew
        result = crew.crew().kickoff(inputs=inputs)
        
        # Extract all task outputs
        print("\n" + "="*60)
        print("[*] Task Execution Summary")
        print("="*60)
        
        if hasattr(result, 'tasks_output') and result.tasks_output:
            classification_result = None
            processing_result = None
            
            for idx, task_output in enumerate(result.tasks_output):
                task_name = task_output.name if hasattr(task_output, 'name') else f"Task {idx+1}"
                output_text = task_output.raw if hasattr(task_output, 'raw') else str(task_output)
                
                print(f"\n[{idx+1}] {task_name}")
                print("-" * 60)
                
                # Skip if output is the skip message
                if "SKIPPED_NO_OUTPUT" in output_text:
                    print("  Status: SKIPPED (not matching document type)")
                    continue
                
                # Print first 200 chars of output
                preview = output_text[:200] + "..." if len(output_text) > 200 else output_text
                print(f"  Output: {preview}")
                
                # Save classification result
                if "classification" in task_name.lower() or idx == 0:
                    classification_result = output_text
                    print("  Type: CLASSIFICATION")
                # Save the first non-skipped processing result
                elif processing_result is None and len(output_text) > 100:
                    processing_result = output_text
                    print("  Type: PROCESSING (Extracted Data)")
            
            # Save processing result to JSON file
            if processing_result:
                import json
                from pathlib import Path
                
                # Determine output filename
                doc_path = Path(document_path)
                output_filename = f"{doc_path.stem}_result.json"
                
                # Try to parse as JSON, if it fails save as raw text
                try:
                    # Check if it's already valid JSON
                    if processing_result.strip().startswith('{'):
                        json_data = json.loads(processing_result)
                    else:
                        # Try to extract JSON from text
                        import re
                        json_match = re.search(r'\{.*\}', processing_result, re.DOTALL)
                        if json_match:
                            json_data = json.loads(json_match.group())
                        else:
                            json_data = {"raw_output": processing_result}
                    
                    # Save to file
                    with open(output_filename, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, indent=2, ensure_ascii=False)
                    
                    print("\n" + "="*60)
                    print(f"[OK] Result saved to: {output_filename}")
                    print("="*60)
                    
                except json.JSONDecodeError:
                    # Save as raw text if JSON parsing fails
                    with open(output_filename, 'w', encoding='utf-8') as f:
                        f.write(processing_result)
                    print("\n" + "="*60)
                    print(f"[OK] Raw result saved to: {output_filename}")
                    print("="*60)
        
        print("\n" + "="*60)
        print("[OK] Processing Complete!")
        print("="*60)
        print("\nFinal Result:")
        print(result)
        print("\n" + "="*60)
        
    except Exception as e:
        import traceback
        print("\n" + "="*60)
        print(f"[ERROR] Error during processing: {str(e)}")
        print("="*60)
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)


def main():
    """
    Command-line interface for the document processing application.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Document Processing System - Classify and extract data from invoices, receipts, and purchase orders"
    )
    
    parser.add_argument(
        'document',
        nargs='?',
        default=None,
        help='Path to the document file to process (PDF, PNG, JPG, etc.)'
    )
    
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate configuration without processing a document'
    )
    
    args = parser.parse_args()
    
    if args.validate_only:
        print("[*] Validating configuration...")
        if validate_environment_variables():
            print("[OK] All configuration is valid!")
        return
    
    run(args.document)


if __name__ == "__main__":
    main()