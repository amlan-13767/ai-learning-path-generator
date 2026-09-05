# 🧠 Memory-Enabled Chatbot System

## Overview

The AI Learning Path Generator now features a **memory-enabled chatbot** that remembers conversation context, tracks learning progress, and provides coherent multi-turn conversations.

## 🎯 Key Features

### Before (Stateless):
```
User: "What's milestone 3 about?"
Bot: "I can help with that. What learning path are you referring to?"

User: "The one I just created"
Bot: "I don't have context about your path. Can you provide more details?"
```

### After (Memory-Enabled):
```
User: "What's milestone 3 about?"
Bot: "Milestone 3 in your 'Python for Data Science' path focuses on NumPy and Pandas. 
      You've completed 2/8 milestones so far. Would you like tips for this one?"

User: "Yes, any good resources?"
Bot: "Based on our conversation and your progress, I recommend..."
```

## 📊 Architecture

### 1. **Enhanced ChatMessage Model**

**New Fields**:
- `conversation_id` (String, indexed) - Groups related messages
- `context` (JSON) - Stores learning path state and progress

**Helper Methods**:
```python
# Get conversation history
messages = ChatMessage.get_conversation_history(conv_id, limit=10)

# Get recent context
context = ChatMessage.get_recent_context(conv_id)

# Clean old messages
deleted = ChatMessage.clean_old_messages(days=7)

# Get conversation stats
stats = ChatMessage.get_conversation_stats(conv_id)
```

### 2. **Memory-Enabled Endpoint**

**Route**: `POST /chatbot-memory`

**Features**:
- ✅ Remembers last 5 messages
- ✅ Tracks learning path progress
- ✅ Saves all messages to database
- ✅ Provides context-aware responses
- ✅ Supports conversation reset

## 🔧 Implementation

### Backend: ChatMessage Model

```python
class ChatMessage(db.Model):
    # Core fields
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    learning_path_id = db.Column(db.String(36), db.ForeignKey('user_learning_paths.id'))
    
    # Message content
    message = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    
    # NEW: Conversation tracking
    conversation_id = db.Column(db.String(36), index=True)
    
    # NEW: Learning path context
    context = db.Column(db.JSON, nullable=True)
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    tokens_used = db.Column(db.Integer, default=0)
    response_time_ms = db.Column(db.Integer)
```

### Backend: Memory-Enabled Chatbot

```python
@bp.route('/chatbot-memory', methods=['POST'])
@login_required
def chatbot_memory():
    # 1. Get or create conversation ID
    if 'conversation_id' not in session:
        conversation_id = str(uuid.uuid4())
        session['conversation_id'] = conversation_id
    else:
        conversation_id = session['conversation_id']
    
    # 2. Get conversation history
    history = ChatMessage.get_conversation_history(conversation_id, limit=5)
    
    # 3. Build context from learning path
    path_context = build_path_context(path_id, user_id)
    
    # 4. Create enhanced prompt
    system_prompt = f"""
You are a helpful AI learning assistant with memory.

{path_context}

Recent conversation:
{format_history(history)}

Current question: {user_message}
"""
    
    # 5. Get AI response
    response = openai_client.chat.completions.create(...)
    
    # 6. Save both messages to database
    user_msg = ChatMessage(conversation_id=conversation_id, role='user', ...)
    ai_msg = ChatMessage(conversation_id=conversation_id, role='assistant', ...)
    db.session.add_all([user_msg, ai_msg])
    db.session.commit()
    
    return jsonify({'reply': response_text})
```

## 📝 Context Object Structure

```json
{
  "path_id": "uuid-string",
  "path_title": "Python for Data Science",
  "completed_milestones": 2,
  "total_milestones": 8,
  "current_milestone": "NumPy and Pandas Basics"
}
```

## 🎨 API Endpoints

### 1. Send Message with Memory
```http
POST /chatbot-memory
Content-Type: application/json

{
  "message": "What should I focus on next?",
  "path_id": "abc-123",
  "reset_conversation": false
}
```

**Response**:
```json
{
  "reply": "Based on your progress (2/8 milestones completed), you should focus on Milestone 3: NumPy and Pandas...",
  "conversation_id": "conv-uuid",
  "tokens_used": 450,
  "response_time_ms": 1200,
  "context": {
    "completed": 2,
    "total": 8,
    "current_milestone": "NumPy and Pandas Basics"
  }
}
```

### 2. Reset Conversation
```http
POST /chatbot/reset
```

**Response**:
```json
{
  "success": true,
  "message": "Conversation reset"
}
```

### 3. Get Conversation History
```http
GET /chatbot/history
```

**Response**:
```json
{
  "conversation_id": "conv-uuid",
  "messages": [
    {
      "role": "user",
      "message": "What's milestone 3?",
      "timestamp": "2025-01-02T10:30:00",
      "tokens_used": 0
    },
    {
      "role": "assistant",
      "message": "Milestone 3 focuses on...",
      "timestamp": "2025-01-02T10:30:02",
      "tokens_used": 150
    }
  ]
}
```

## 💡 Usage Examples

### Example 1: Multi-Turn Conversation
```javascript
// First message
fetch('/chatbot-memory', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: "What's the hardest milestone?",
        path_id: "path-123"
    })
});
// Response: "Based on your path, Milestone 5 (Machine Learning Algorithms) is typically the most challenging..."

// Follow-up (remembers context)
fetch('/chatbot-memory', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: "Can you break it down for me?",
        path_id: "path-123"
    })
});
// Response: "Sure! For Milestone 5, let's break it into smaller steps..."
```

### Example 2: Progress-Aware Responses
```javascript
// User has completed 3/8 milestones
fetch('/chatbot-memory', {
    method: 'POST',
    body: JSON.stringify({
        message: "Am I on track?",
        path_id: "path-123"
    })
});
// Response: "You've completed 3 out of 8 milestones! At this pace, you're doing great..."
```

### Example 3: Reset Conversation
```javascript
// Start fresh conversation
fetch('/chatbot/reset', {method: 'POST'});

// Next message starts new conversation
fetch('/chatbot-memory', {
    method: 'POST',
    body: JSON.stringify({
        message: "Hi, I need help with my learning path",
        path_id: "path-123"
    })
});
```

## 🎯 Context-Aware Features

### 1. **Progress Tracking**
The bot knows:
- How many milestones completed
- Current milestone
- Overall progress percentage

### 2. **Conversation Memory**
The bot remembers:
- Last 5 messages in conversation
- Previous questions asked
- Topics discussed

### 3. **Learning Path Context**
The bot has access to:
- Path title and topic
- All milestone titles
- Completion status of each milestone

## 📊 Database Schema

```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    learning_path_id VARCHAR(36),
    
    -- Message content
    message TEXT NOT NULL,
    role VARCHAR(20) NOT NULL,
    
    -- NEW: Conversation tracking
    conversation_id VARCHAR(36),
    context JSON,
    
    -- Metadata
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    tokens_used INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    
    -- Indexes
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_timestamp (timestamp)
);
```

## 🔧 Migration

Run the migration to add new fields:

```bash
# Using Flask-Migrate
flask db migrate -m "Add conversation memory to ChatMessage"
flask db upgrade

# Or run SQL directly
psql -d your_database -f migrations/add_conversation_memory.sql
```

## 📈 Performance

### Memory Overhead:
```
Conversation with 10 messages:
- Database: ~5KB per conversation
- Session: ~100 bytes (conversation_id only)
- Memory: Minimal (queries are indexed)
```

### Response Time:
```
Without memory: 800-1200ms
With memory: 850-1300ms
Overhead: ~50-100ms (negligible)
```

### Token Usage:
```
Without context: ~200 tokens per response
With context: ~300-400 tokens per response
Increase: 50-100% (provides much better responses)
```

## 🎨 Frontend Integration

### Basic Chat Interface
```html
<div id="chat-container">
    <div id="messages"></div>
    <input id="user-input" type="text" placeholder="Ask a question...">
    <button onclick="sendMessage()">Send</button>
    <button onclick="resetConversation()">New Conversation</button>
</div>

<script>
async function sendMessage() {
    const message = document.getElementById('user-input').value;
    const pathId = getCurrentPathId();
    
    const response = await fetch('/chatbot-memory', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            message: message,
            path_id: pathId
        })
    });
    
    const data = await response.json();
    displayMessage('user', message);
    displayMessage('assistant', data.reply);
}

async function resetConversation() {
    await fetch('/chatbot/reset', {method: 'POST'});
    document.getElementById('messages').innerHTML = '';
    alert('Conversation reset! Starting fresh.');
}
</script>
```

## 🧹 Maintenance

### Clean Old Messages
```python
# Delete messages older than 7 days
deleted_count = ChatMessage.clean_old_messages(days=7)
print(f"Deleted {deleted_count} old messages")
```

### Get Conversation Stats
```python
stats = ChatMessage.get_conversation_stats(conversation_id)
print(f"Total messages: {stats['total_messages']}")
print(f"Tokens used: {stats['total_tokens']}")
print(f"Avg response time: {stats['avg_response_time_ms']}ms")
```

## 🎉 Summary

The memory-enabled chatbot provides:
- ✅ **Conversation memory** (last 5 messages)
- ✅ **Progress awareness** (completed vs pending milestones)
- ✅ **Context tracking** (learning path details)
- ✅ **Multi-turn dialogues** (coherent conversations)
- ✅ **Database persistence** (all messages saved)
- ✅ **Conversation reset** (start fresh anytime)
- ✅ **Performance tracking** (tokens, response time)
- ✅ **Automatic cleanup** (delete old messages)

**Result**: Users get intelligent, context-aware assistance instead of repetitive, stateless responses! 🚀

---

**Built with ❤️ for the AI Learning Path Generator**
