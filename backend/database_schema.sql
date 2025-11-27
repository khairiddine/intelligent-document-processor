"""
Supabase Database Schema (SQL)
Run this in your Supabase SQL Editor
"""

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Documents Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  filename VARCHAR(255) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  file_size INTEGER,
  upload_timestamp TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ,
  status VARCHAR(50) DEFAULT 'pending',
  document_type VARCHAR(50),
  phoenix_trace_id VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);

-- ============================================================================
-- Extraction Results Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS extraction_results (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  result_data JSONB,
  vendor_name VARCHAR(255),
  total_amount DECIMAL(10,2),
  invoice_date DATE,
  confidence_score DECIMAL(3,2),
  processing_duration_seconds INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_extraction_document_id ON extraction_results(document_id);

-- ============================================================================
-- Processing History Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS processing_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  agent_used VARCHAR(100),
  success BOOLEAN DEFAULT true,
  error_message TEXT,
  phoenix_trace_url VARCHAR(500),
  processed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_processing_history_user_id ON processing_history(user_id);
CREATE INDEX idx_processing_history_document_id ON processing_history(document_id);

-- ============================================================================
-- AG-UI Interactions Table (Optional - for persistent storage)
-- ============================================================================
CREATE TABLE IF NOT EXISTS agui_interactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id VARCHAR(255) NOT NULL,
  document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  action_type VARCHAR(50),
  agent_message TEXT,
  user_response VARCHAR(50),
  agent_result JSONB,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_agui_session_id ON agui_interactions(session_id);
CREATE INDEX idx_agui_document_id ON agui_interactions(document_id);

-- ============================================================================
-- Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE extraction_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE agui_interactions ENABLE ROW LEVEL SECURITY;

-- Documents: Users can only see their own documents
CREATE POLICY "Users can view own documents"
  ON documents FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own documents"
  ON documents FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own documents"
  ON documents FOR UPDATE
  USING (auth.uid() = user_id);

-- Extraction Results: Users can only see results for their documents
CREATE POLICY "Users can view own extraction results"
  ON extraction_results FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM documents
      WHERE documents.id = extraction_results.document_id
      AND documents.user_id = auth.uid()
    )
  );

-- Processing History: Users can only see their own history
CREATE POLICY "Users can view own processing history"
  ON processing_history FOR SELECT
  USING (auth.uid() = user_id);

-- AG-UI Interactions: Users can only see their own interactions
CREATE POLICY "Users can view own agui interactions"
  ON agui_interactions FOR SELECT
  USING (auth.uid() = user_id);

-- ============================================================================
-- Storage Bucket for Documents
-- ============================================================================
-- Run this in Supabase Dashboard -> Storage -> Create Bucket
-- Bucket name: documents
-- Public: false (private)

-- RLS for Storage
-- In Supabase Dashboard -> Storage -> documents -> Policies

-- Policy 1: Users can upload to their own folder
CREATE POLICY "Users can upload own documents"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'documents' AND
    (storage.foldername(name))[1] = auth.uid()::text
  );

-- Policy 2: Users can read their own documents
CREATE POLICY "Users can read own documents"
  ON storage.objects FOR SELECT
  USING (
    bucket_id = 'documents' AND
    (storage.foldername(name))[1] = auth.uid()::text
  );
