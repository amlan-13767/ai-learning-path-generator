-- Migration: Add Conversation Memory to ChatMessage Model
-- Date: 2025-01-02
-- Description: Adds conversation_id and context fields for memory-enabled chatbot

-- Add conversation_id column (groups related messages)
ALTER TABLE chat_messages ADD COLUMN conversation_id VARCHAR(36);

-- Add context column (stores learning path context as JSON)
ALTER TABLE chat_messages ADD COLUMN context JSON;

-- Create index on conversation_id for fast queries
CREATE INDEX idx_chat_messages_conversation_id ON chat_messages(conversation_id);

-- Update existing records to use session_id as conversation_id (backward compatibility)
UPDATE chat_messages SET conversation_id = session_id WHERE session_id IS NOT NULL;

-- Add comments
COMMENT ON COLUMN chat_messages.conversation_id IS 'Groups related messages in a conversation';
COMMENT ON COLUMN chat_messages.context IS 'Stores learning path state, progress, and milestone data';
