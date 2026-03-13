---
name: "macos-calendar-event-creator"
description: "Extracts calendar event information from natural language text and generates AppleScript to create macOS Calendar events. Invoke when user wants to create calendar events from text descriptions on macOS."
---

# macOS Calendar Event Creator

This skill extracts structured calendar event information from natural language text and generates executable AppleScript code to create events in macOS Calendar app.

## When to Use

- User provides text describing a calendar event (e.g., "明天下午3点开会")
- User wants to create a macOS Calendar event from natural language
- User needs to convert text descriptions into calendar entries

## Required Context

**CRITICAL**: This skill requires the current system date to accurately parse relative dates (like "明天", "下周一"). 

The execution environment MUST provide the current date in the context. Include this information when invoking the skill:

```
Current system date: 2026-03-13 (YYYY-MM-DD format)
Current system time: 14:30 (optional, for time reference)
```

**Without the system date, the skill cannot accurately calculate relative dates.**

## How It Works

1. **Extract Information**: Parse the user's text to extract event details
2. **Generate AppleScript**: Create AppleScript code that creates the calendar event
3. **Output**: Provide the AppleScript code for the system to execute

## Extraction Rules

### Required Fields

| Field | Format | Description |
|-------|--------|-------------|
| `title` | string | Event title (concise, 1-5 keywords) |
| `start_time` | YYYY-MM-DD HH:MM:SS | Event start time (24-hour format) |
| `end_time` | YYYY-MM-DD HH:MM:SS | Event end time (24-hour format) |
| `location` | string or null | Event location (if mentioned) |
| `description` | string or null | Event description |

### Time Processing Rules

**CRITICAL: System Date Dependency**

You MUST obtain the current system date from the execution environment before parsing any time information. **DO NOT** use your training data's knowledge of dates. All date calculations must be based on the actual system current date.

**How to Get System Date**:
- The execution environment should provide current date (e.g., via environment variables, system calls, or context)
- If not provided, ask the system for current date using: `date +%Y-%m-%d` or equivalent

**Date Calculation Rules**:

1. **Always Base on System Current Date**:
   - Current system date is your ONLY reference point
   - All relative dates ("明天", "下周一", etc.) must be calculated from this date
   - Never assume or hallucinate the current date

2. **Relative Date Parsing** (calculate from system current date):
   - "明天" → Current date + 1 day
   - "后天" → Current date + 2 days
   - "下周一" → Next Monday from current date
   - "这周末" → This Saturday from current date
   - "下周三下午" → Next Wednesday from current date
   - "大后天" → Current date + 3 days

3. **Year Handling**:
   - If date mentioned without year (e.g., "1月15日") → Use current year from system date
   - If "明年" explicitly mentioned → Use current year + 1
   - If "去年" explicitly mentioned → Use current year - 1

4. **Month/Day Handling**:
   - If mentioned date has already passed in current year (e.g., current is March, user says "1月15日") → Use next year
   - If mentioned date is today → Use today
   - If mentioned date is in the future → Use current year

**Default Start Times** (when not specified):
- Meeting/Work events → 09:00
- Leisure/Entertainment/Sports → 14:00
- Meals/Dining → 12:00 (lunch) or 18:00 (dinner)
- Unknown type → 09:00

**Default Durations** (when not specified):
- Meeting → 1 hour
- Interview → 1 hour
- Training/Course → 2 hours
- Sports/Fitness → 1 hour
- Meals → 1 hour
- Other → 1 hour

### Title Extraction Rules

Title must be extremely concise:
- Keep only the core 1-5 keywords
- Remove all time, location, and people information
- Keep only the core action and subject
- Remove all modifiers and details

**Examples**:
- "明天下午3点和张三开会讨论项目进度" → "项目进度会议"
- "下周二上午10点在会议室A参加产品评审会议" → "产品评审"
- "周五下午2点去健身房锻炼" → "健身"
- "今天晚上7点和家人一起吃晚饭" → "晚饭"

## Output Format

After extracting the information, generate AppleScript code in this exact format:

```applescript
tell application "Calendar"
    tell calendar "Home"
        make new event with properties {summary:"EVENT_TITLE", start date:date "START_TIME", end date:date "END_TIME", description:"DESCRIPTION", location:"LOCATION"}
    end tell
end tell
```

**Important Notes**:
1. Replace `EVENT_TITLE`, `START_TIME`, `END_TIME`, `DESCRIPTION`, and `LOCATION` with actual values
2. Time format must be: `YYYY-MM-DD HH:MM:SS` (e.g., "2026-03-14 15:00:00")
3. Escape double quotes in strings by replacing `"` with `\"`
4. If location or description is null, omit those properties from the AppleScript
5. The calendar name "Home" can be changed to the user's preferred calendar name

## Example Usage

### Example 1: With System Date Context

**System Context Provided**:
```
Current system date: 2026-03-13
```

**User Input**: "明天下午3点到5点和张三在会议室A开会讨论项目进度"

**Calculation Process**:
1. System date: 2026-03-13
2. "明天" = 2026-03-13 + 1 day = 2026-03-14
3. "下午3点" = 15:00
4. "到5点" = 17:00 (2 hours duration)

**Extracted Information**:
- Title: "项目进度会议"
- Start Time: "2026-03-14 15:00:00"
- End Time: "2026-03-14 17:00:00"
- Location: "会议室A"
- Description: "与张三讨论项目进度"

**Generated AppleScript**:
```applescript
tell application "Calendar"
    tell calendar "Home"
        make new event with properties {summary:"项目进度会议", start date:date "2026-03-14 15:00:00", end date:date "2026-03-14 17:00:00", description:"与张三讨论项目进度", location:"会议室A"}
    end tell
end tell
```

### Example 2: Date Already Passed

**System Context Provided**:
```
Current system date: 2026-03-13
```

**User Input**: "1月15号下午2点开会"

**Calculation Process**:
1. System date: 2026-03-13 (March)
2. "1月15号" has already passed in current year (January < March)
3. Therefore use next year: 2027-01-15
4. "下午2点" = 14:00

**Extracted Information**:
- Title: "会议"
- Start Time: "2027-01-15 14:00:00"
- End Time: "2027-01-15 15:00:00" (default 1 hour for meetings)
- Location: null
- Description: null

**Generated AppleScript**:
```applescript
tell application "Calendar"
    tell calendar "Home"
        make new event with properties {summary:"会议", start date:date "2027-01-15 14:00:00", end date:date "2027-01-15 15:00:00"}
    end tell
end tell
```

## Execution Instructions

Provide the generated AppleScript code to the user or system. The code can be executed on macOS using:
- `osascript -e 'APPLESCRIPT_CODE'` (command line)
- Direct execution in Script Editor
- Automation tools like OpenClaw, Hammerspoon, etc.
