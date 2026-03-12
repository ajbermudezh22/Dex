# /linear-setup - Connect Linear to Dex

## Purpose
Guide users through connecting Linear to Dex using Claude Code's built-in OAuth. No API key needed — just click and authorize.

## When to Use
- User says "connect linear", "set up linear", "integrate linear"
- During onboarding when user indicates they use Linear
- When user asks about issues, tickets, sprints, or cycles

## Prerequisites
- Linear account (any role — no admin required)
- Claude Code CLI or Claude Desktop (OAuth is built-in)

## Flow

### Step 1: Check Existing Connection

Try calling `mcp__linear__list_teams` to see if Linear is already connected.

**If it responds with team data:**
```
✅ Linear is already connected! I can see your workspace: [team name(s)]

Want me to:
1. Show your assigned issues
2. Test the full connection
3. Reconfigure preferences
```
→ Skip to Step 5 (Capability Cascade)

**If the tool is not available or errors:**
→ Continue to Step 2

### Step 2: Guide OAuth Connection

Say:

```
Let's connect Linear — this takes about 30 seconds, no API key needed.

**Type `/mcp` in the chat**, then:
1. Find **Linear** in the list
2. Click **Connect**
3. Sign in with your Linear account in the browser
4. Come back here when you see "Connected" ✓

I'll wait here!
```

**Important:** Do NOT try to automate this step. The `/mcp` flow handles OAuth securely through Claude Code's built-in system.

### Step 3: Verify Connection

After user returns, verify by calling `mcp__linear__list_teams`.

**If successful:**
```
✅ Connected! I can see your Linear workspace: [team name(s)]
```
→ Continue to Step 4

**If it fails:**
```
Hmm, I can't reach Linear yet. A few things to check:
- Did the browser show "Authorization successful"?
- Try running `/mcp` again and reconnecting Linear
- Make sure you authorized the correct Linear workspace
```

### Step 4: Configure Preferences (Task Sync)

Ask trust level for issue management:

```
How hands-on do you want me to be with Linear issues?

1. **"Show me first"** — I'll surface your issues in plans and prep, but won't create or modify anything in Linear (recommended to start)
2. **"Keep them in sync"** — Create Linear issues from meeting action items automatically
3. **"Only pull in"** — Show me issues for context, but never write to Linear
```

Store choice in `System/integrations/config.yaml` under `linear.trust_level`:
- `confirm_each` → Show me first
- `autonomous` → Keep them in sync
- `read_only` → Only pull in

### Step 5: Update Config

Update `System/integrations/config.yaml`:
- Set `linear: true` under `enabled`
- Update `last_updated` timestamp
- Store trust_level preference

### Step 6: Capability Cascade (Delight Moment)

```
**Linear is connected!** Here's what just changed:

### Enhanced (existing skills that got smarter)
- **`/daily-plan`** → Shows your assigned issues and current cycle progress
- **`/meeting-prep`** → Pulls open issues for attendees' teams
- **`/week-plan`** → Includes cycle goals in weekly priorities

### New Superpowers
- 📋 **Issue Lookup** — "Show my Linear tickets" or "What's assigned to me?"
- 🔍 **Project Status** — "What's the status of [project]?" pulls live data
- 🏃 **Sprint Awareness** — Current cycle progress in daily/weekly plans
- 👥 **Team Context** — See what teammates are working on before meetings

### How It Works
- **Reading:** Your issues and projects appear automatically in plans and prep
- **Writing:** [Based on trust level choice above]
- **Privacy:** Auth is managed by Claude Code — no tokens stored in your vault

Try it now: **"Show my open tickets"**
```

## Key Messages

**Success:**
> ✅ Linear connected via OAuth! No API key, no config files, no restarts needed.
> Your issues will appear in daily plans, meeting prep, and weekly priorities.

**Already Connected:**
> Linear is already connected. Want me to show your tickets or reconfigure preferences?

**Connection Failed:**
> Linear isn't connecting. Try `/mcp` → disconnect Linear → reconnect. If that doesn't work, check that you're signed into the right Linear workspace.

## Error Handling

| Error | Response |
|-------|----------|
| Tool not available | "Linear MCP isn't available yet. Type `/mcp` and connect Linear first." |
| Auth expired | "Your Linear session may have expired. Run `/mcp` and reconnect Linear." |
| No teams found | "Connected but no teams visible. Check your Linear workspace permissions." |
| Rate limited | "Linear is rate-limiting requests. Wait a minute and try again." |

## What Makes This Different

Unlike Notion/Slack/Google integrations, Linear uses **Claude Code's built-in OAuth**:
- No API key to create or manage
- No npx package to install
- No Claude Desktop config to edit
- No restart required
- Token refresh is automatic

This is the simplest integration in Dex.

## Analytics Event
```python
fire_event('integration_linear_completed', {
    'auth_type': 'oauth_builtin',
    'trust_level': 'confirm_each' | 'autonomous' | 'read_only'
})
```

## Related Skills
- `/integrate-slack` - Connect Slack
- `/integrate-notion` - Connect Notion
- `/integrate-google` - Connect Google Workspace
- `/daily-plan` - Uses Linear context when available
- `/meeting-prep` - Pulls Linear issues for attendees
