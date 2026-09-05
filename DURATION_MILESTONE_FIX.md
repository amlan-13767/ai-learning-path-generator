# 🕒 Duration & Milestone Scaling Fix

## Problem Identified

**Issue:** Learning paths always generated 14 weeks and 5 milestones, regardless of the user's duration selection on the homepage.

**Root Cause:** The `duration_weeks` field from the form was not being:
1. Extracted from form data in `main_routes.py`
2. Passed to the `generate_path()` function
3. Used in milestone calculation
4. Communicated to the AI model in the prompt

---

## Fixes Applied

### 1. **Extract Duration from Form**
**File:** `web_app/main_routes.py` (lines 109-118)

#### Before:
```python
topic = data.get('topic')
expertise = data.get('expertise_level')
style = data.get('learning_style')
time_commitment = data.get('time_commitment')
# duration_weeks was NOT being extracted!
```

#### After:
```python
topic = data.get('topic')
expertise = data.get('expertise_level')
style = data.get('learning_style')
time_commitment = data.get('time_commitment')
duration_weeks = data.get('duration_weeks')  # Extract user-specified duration

# Convert to int if provided
if duration_weeks:
    try:
        duration_weeks = int(duration_weeks)
    except ValueError:
        duration_weeks = None
```

---

### 2. **Pass Duration to generate_path()**
**File:** `web_app/main_routes.py` (line 134)

#### Before:
```python
learning_path = path_generator.generate_path(
    topic=topic,
    expertise_level=expertise,
    learning_style=style,
    time_commitment=time_commitment,
    # duration_weeks NOT passed!
    ai_provider=ai_provider,
    ai_model=ai_model
)
```

#### After:
```python
learning_path = path_generator.generate_path(
    topic=topic,
    expertise_level=expertise,
    learning_style=style,
    time_commitment=time_commitment,
    duration_weeks=duration_weeks,  # Pass user-specified duration
    ai_provider=ai_provider,
    ai_model=ai_model
)
```

---

### 3. **Add duration_weeks Parameter**
**File:** `src/learning_path.py` (line 238)

#### Before:
```python
def generate_path(
    self,
    topic: str,
    expertise_level: str,
    learning_style: str,
    time_commitment: str = "moderate",
    # duration_weeks parameter missing!
    goals: List[str] = None,
    ...
) -> LearningPath:
```

#### After:
```python
def generate_path(
    self,
    topic: str,
    expertise_level: str,
    learning_style: str,
    time_commitment: str = "moderate",
    duration_weeks: Optional[int] = None,  # New parameter
    goals: List[str] = None,
    ...
) -> LearningPath:
```

---

### 4. **Use User Duration or Calculate**
**File:** `src/learning_path.py` (lines 285-309)

#### Before:
```python
# Always calculated, never used user input
adjusted_duration = int(
    base_duration
    * intensity_factor.get(time_commitment, 1.0)
    * complexity_factor.get(expertise_level, 1.0)
)
# Result: Always same duration for same inputs
```

#### After:
```python
# Use user-specified duration if provided, otherwise calculate
if duration_weeks and duration_weeks > 0:
    adjusted_duration = duration_weeks
    print(f"✅ Using user-specified duration: {adjusted_duration} weeks")
else:
    # Fallback to calculation
    adjusted_duration = int(
        base_duration
        * intensity_factor.get(time_commitment, 1.0)
        * complexity_factor.get(expertise_level, 1.0)
    )
    print(f"📊 Calculated duration: {adjusted_duration} weeks")
```

---

### 5. **Dynamic Milestone Calculation**
**File:** `src/learning_path.py` (lines 311-324)

#### New Logic:
```python
# Calculate appropriate number of milestones based on duration
# Rule: 1 milestone per 1-3 weeks
if adjusted_duration <= 4:
    target_milestones = 3  # Short paths: 3 milestones
elif adjusted_duration <= 8:
    target_milestones = 4  # Medium paths: 4 milestones
elif adjusted_duration <= 12:
    target_milestones = 5  # Standard paths: 5 milestones
elif adjusted_duration <= 20:
    target_milestones = 6  # Long paths: 6 milestones
else:
    target_milestones = 7  # Very long paths: 7 milestones

print(f"🎯 Target milestones for {adjusted_duration} weeks: {target_milestones}")
```

**Milestone Scaling Table:**

| Duration (weeks) | Milestones | Weeks per Milestone |
|------------------|------------|---------------------|
| 1-4              | 3          | 1-1.3               |
| 5-8              | 4          | 1.25-2              |
| 9-12             | 5          | 1.8-2.4             |
| 13-20            | 6          | 2.2-3.3             |
| 21+              | 7          | 3+                  |

---

### 6. **Update AI Prompt**
**File:** `src/learning_path.py` (lines 328-343)

#### Before:
```python
prompt_content = f"""Generate a detailed personalized learning path for the following:

Topic: {topic}
Expertise Level: {expertise_level}
Learning Style: {learning_style}
Time Commitment: {time_commitment}
Learning Goals: {', '.join(goals)}
Additional Information: {additional_info or 'None provided'}

IMPORTANT: Return ONLY valid JSON matching this exact structure.
"""
```

#### After:
```python
prompt_content = f"""Generate a detailed personalized learning path for the following:

Topic: {topic}
Expertise Level: {expertise_level}
Learning Style: {learning_style}
Time Commitment: {time_commitment}
Duration: {adjusted_duration} weeks
Target Milestones: {target_milestones} milestones
Learning Goals: {', '.join(goals)}
Additional Information: {additional_info or 'None provided'}

IMPORTANT: 
1. Return ONLY valid JSON matching this exact structure.
2. Generate EXACTLY {target_milestones} milestones (no more, no less).
3. Set duration_weeks to EXACTLY {adjusted_duration}.
4. Distribute the milestones evenly across the {adjusted_duration} weeks.
"""
```

**Impact:** AI now has explicit instructions about duration and milestone count.

---

## How It Works Now

### Example 1: Short Path (2 weeks)
```
User Input: 2 weeks
System Response:
  ✅ Using user-specified duration: 2 weeks
  🎯 Target milestones for 2 weeks: 3
  
Result:
  - Duration: 2 weeks
  - Milestones: 3
  - Distribution: ~0.7 weeks per milestone
```

### Example 2: Standard Path (12 weeks)
```
User Input: 12 weeks
System Response:
  ✅ Using user-specified duration: 12 weeks
  🎯 Target milestones for 12 weeks: 5
  
Result:
  - Duration: 12 weeks
  - Milestones: 5
  - Distribution: ~2.4 weeks per milestone
```

### Example 3: Long Path (24 weeks)
```
User Input: 24 weeks
System Response:
  ✅ Using user-specified duration: 24 weeks
  🎯 Target milestones for 24 weeks: 7
  
Result:
  - Duration: 24 weeks
  - Milestones: 7
  - Distribution: ~3.4 weeks per milestone
```

### Example 4: No Duration (Calculated)
```
User Input: (blank)
System Response:
  📊 Calculated duration: 14 weeks
  🎯 Target milestones for 14 weeks: 6
  
Result:
  - Duration: 14 weeks (calculated)
  - Milestones: 6
  - Distribution: ~2.3 weeks per milestone
```

---

## Testing the Fix

### 1. **Restart Flask:**
```powershell
# Stop Flask (Ctrl+C)
python run_flask.py
```

### 2. **Test Short Path:**
- Topic: "Python Basics"
- Duration: **2 weeks**
- Expected: 3 milestones

### 3. **Test Medium Path:**
- Topic: "Web Development"
- Duration: **8 weeks**
- Expected: 4 milestones

### 4. **Test Standard Path:**
- Topic: "Machine Learning"
- Duration: **12 weeks**
- Expected: 5 milestones

### 5. **Test Long Path:**
- Topic: "Deep Learning"
- Duration: **24 weeks**
- Expected: 7 milestones

### 6. **Watch Terminal Logs:**
```
✅ Using user-specified duration: 8 weeks
🎯 Target milestones for 8 weeks: 4
📊 Fetching job market data for main topic: Web Development
🔍 Fetching resources for 4 milestones in parallel...
  [1/4] Fetching resources for: Web Development: HTML Basics
  [2/4] Fetching resources for: Web Development: CSS Styling
  [3/4] Fetching resources for: Web Development: JavaScript Fundamentals
  [4/4] Fetching resources for: Web Development: React Framework
✅ All resources fetched!
```

---

## Validation Points

### ✅ Form Input:
- Duration input field exists in `index.html`
- Field name: `duration_weeks`
- Type: `number` (min=1, max=52)

### ✅ Backend Processing:
- `main_routes.py` extracts `duration_weeks`
- Converts to `int` safely
- Passes to `generate_path()`

### ✅ Learning Path Generation:
- Accepts `duration_weeks` parameter
- Uses user value if provided
- Falls back to calculation if not
- Scales milestones dynamically

### ✅ AI Prompt:
- Includes target duration
- Includes target milestone count
- Has explicit instructions to follow counts

---

## Edge Cases Handled

1. **No duration provided:** Falls back to calculated duration
2. **Invalid duration (non-number):** Catches ValueError, uses calculation
3. **Zero or negative duration:** Uses calculation
4. **Very short duration (1 week):** Minimum 3 milestones
5. **Very long duration (52 weeks):** Maximum 7 milestones

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Duration Source** | Always calculated | User input or calculated |
| **Duration Value** | Always ~14 weeks | Respects user choice |
| **Milestone Count** | Always ~5 | Scales 3-7 based on duration |
| **User Control** | None | Full control via form |
| **Fallback** | N/A | Calculation if no input |

---

## Expected Terminal Output

```
✅ Using user-specified duration: 8 weeks
🎯 Target milestones for 8 weeks: 4
📊 Fetching job market data for main topic: Python
🔍 Fetching resources for 4 milestones in parallel...
  [1/4] Fetching resources for: Python: Setup & Basics
  [2/4] Fetching resources for: Python: Data Structures
  [3/4] Fetching resources for: Python: Functions & Modules
  [4/4] Fetching resources for: Python: Project Work
✅ All resources fetched!
```

---

*Last updated: 2025-10-01*
*Files modified: `web_app/main_routes.py`, `src/learning_path.py`*
