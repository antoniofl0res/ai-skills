---
name: review-emails
description: Pull Outlook emails and calendar meetings via COM, triage them, and produce a sitrep (HTML + tasks.json + report.json). Output folder defaults to Downloads/Weekly report/ but is overridable via REVIEW_EMAILS_DIR env var. Default interval is 1 day (26 h window). Pass a number or "weekly" to change: /review-emails 7 or /review-emails weekly.
---

# Review Emails

## Arguments & mode detection

Parse the argument passed to `/review-emails` (if any):

| Invocation | DaysBack | PeriodLabel | ReportType | FileSuffix | UnrepliedThreshold | SlowReplyThreshold |
|---|---|---|---|---|---|---|
| `/review-emails` | 1 | Daily | daily | daily | same-day (all unreplied Tier 1 today) | n/a |
| `/review-emails N` (2â€“6) | N | N-Day | custom | `N`day | âŒŠN/3âŒ‹ days (min 1) | âŒŠN/2âŒ‹ days (min 2) |
| `/review-emails 7` or `/review-emails weekly` | 7 | Weekly | weekly | weekly | 3 days | 4 days |
| `/review-emails N` (N > 7) | N | N-Day | custom | `N`day | âŒŠN/3âŒ‹ days | âŒŠN/2âŒ‹ days |

Derive at the top of every run:

```
DaysBack        = argument or 1
HoursBack       = DaysBack * 26          # 26 h/day buffer â€” never use calendar days for the cutoff
PeriodLabel     = "Daily" if DaysBack=1 else "Weekly" if DaysBack=7 else "${DaysBack}-Day"
ReportType      = "daily" / "weekly" / "custom"
FileSuffix      = "daily" / "weekly" / "${DaysBack}day"
PeriodStart     = now âˆ’ HoursBack hours  # exact datetime, not midnight
PeriodEnd       = now
LookForwardDays = DaysBack   # "Coming Up" window = same length as review window
UnrepliedThreshold = 0 if DaysBack=1 else max(1, floor(DaysBack/3))
SlowThreshold      = max(2, floor(DaysBack/2))

# Output directory â€” override via env var, else use the default
ReportDir       = $env:REVIEW_EMAILS_DIR  if set, else  "$env:USERPROFILE\Downloads\Weekly report"
```

For **daily** runs: flag ALL Tier 1 inbox emails that arrived today with no same-day reply (threshold = 0 means "no grace period").

---

## Step 1 â€” Load the persistent task ledger

`tasks.json` is the single source of truth for open/done/dropped actions. It is shared
with the local dashboard (`dashboard\server.py`). Load it â€” never scrape old HTML for state.

```powershell
$dir = if ($env:REVIEW_EMAILS_DIR) { $env:REVIEW_EMAILS_DIR } else { "$env:USERPROFILE\Downloads\Weekly report" }
$tasksPath = "$dir\tasks.json"
if (Test-Path $tasksPath) {
    Get-Content $tasksPath -Raw -Encoding UTF8
} else {
    '{ "version": 1, "tasks": [] }'
}
```

Hold every task with `status = "open"` as a **carryover candidate** for Step 3.5.
Never alter a task's `status`, `comments`, `resolution`, or user-set `urgent` â€” those are owned by the user.

**One-time seed (empty ledger only).** If `tasks.json` is missing or contains only seed
placeholders (`seed000001` etc.), read the most recent `*-sitrep.html` in `$dir`, extract
genuinely open items from its *Still Open / Carryover* sections, create one task per item
(status=open, `first_seen`/`source.date` = original date, comment = "Backfilled from
\<file\> (pre-ledger)."), then proceed. Do this **once** â€” on later runs the ledger is
authoritative and HTML is ignored.

---

## Step 2 â€” Extract emails and meetings (past period)

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\Antonio Flores\.gemini\config\skills\review-emails\scripts\Get-EmailDigest.ps1" -DaysBack $DaysBack -MaxBodyLength 300
```

If output still exceeds 150 KB, add `-MaxEmails 100 -MaxBodyLength 200` and note truncation
in the report header.

The JSON contains:
- `Emails` â€” `Folder`, `From`, `FromEmail`, `To`, `CC`, `ToCount`, `CCCount`,
  `ConversationTopic`, `Importance`, `Date`, `Body`, `HasAttachments`
- `Meetings` â€” `Role` (Organiser / Accepted), `Start`, `End`, `Duration`,
  `Organizer`, `Required`, `Optional`
- `InboxCount`, `SentCount`, `MeetingCount` â€” verify; flag `SentCount = 0`
- `NoiseFilterOn`, `InboxFilteredCount`, `TopFilteredSenders`, `InboxCapped`

**Noise filtering:** broadcast/newsletter/list mail is filtered before the `-MaxEmails` cap.
SharePoint / Teams / Planner notifications are kept. Sent Items are never filtered.
- `InboxCapped = true` â†’ real mail hit the ceiling; rerun with `-MaxEmails 500`; set
  `stats.capped = true` in report.json.
- `InboxCapped = false` â†’ set `stats.capped = false`, `stats.filtered = InboxFilteredCount`.

---

## Step 2b â€” Fetch upcoming calendar items (next `LookForwardDays` days)

Run this immediately after Step 2 to populate the **Coming Up** section.

```powershell
$daysForward = $LookForwardDays   # same as DaysBack
$ol   = New-Object -ComObject Outlook.Application
$ns   = $ol.GetNamespace("MAPI")
$cal  = $ns.GetDefaultFolder(9)   # olFolderCalendar
$itms = $cal.Items
$itms.IncludeRecurrences = $true
$itms.Sort("[Start]")
$now    = Get-Date
$fwdEnd = $now.AddDays($daysForward)
$filter = "[Start] >= '$($now.ToString("MM/dd/yyyy HH:mm"))' AND [Start] < '$($fwdEnd.ToString("MM/dd/yyyy HH:mm"))'"
# Role MUST come from the actual OlResponseStatus â€” an invite on the calendar is NOT
# necessarily accepted. Never infer Accepted from mere presence on the calendar.
#   0 None Â· 1 Organised Â· 2 Tentative Â· 3 Accepted Â· 4 Declined Â· 5 NotResponded
$rsLabel = @{ 0 = "Not responded"; 1 = "Organiser"; 2 = "Tentative";
              3 = "Accepted";      4 = "Declined";  5 = "Not responded" }
$upcoming = $itms.Restrict($filter) | ForEach-Object {
    $rs = [int]$_.ResponseStatus
    $role = if ($_.MeetingStatus -eq 1 -or $rs -eq 1) { "Organiser" }
            elseif ($rsLabel.ContainsKey($rs)) { $rsLabel[$rs] } else { "Not responded" }
    [PSCustomObject]@{
        Subject   = $_.Subject
        Start     = $_.Start.ToString("yyyy-MM-dd HH:mm")
        End       = $_.End.ToString("yyyy-MM-dd HH:mm")
        Duration  = $_.Duration
        Organizer = $_.Organizer
        Location  = $_.Location
        Required  = $_.RequiredAttendees
        ResponseStatus = $rs
        Role      = $role   # TRUE response status â€” render verbatim, do not relabel as Accepted
    }
} | Where-Object { $_.Duration -gt 0 -and $_.ResponseStatus -ne 4 }   # drop declined
$upcoming | ConvertTo-Json -Depth 5
```

Also extract **deadline signals** from the open task ledger: tasks whose `source.date` or
first-seen date + expected urgency suggests they fall within the look-forward window. List
these alongside the calendar items in Coming Up.

---

## Step 3 â€” Triage emails

Classify every email into tiers **before writing anything**:

### Tier 1 â€” Always include
- `Folder = "Sent Items"` (Antonio's own outputs)
- `ToCount` 1â€“3 AND Antonio is primary recipient
- `Importance = 2` (High)
- Multi-turn threads (same `ConversationTopic` in both Inbox and Sent Items)

### Tier 2 â€” Include if substantive
- `ToCount` 4â€“8, Antonio in To
- `HasAttachments = true`
- First message in a thread from a named individual

### Tier 3 â€” Background only (do not include in narrative)
- Antonio in CC only
- Distribution lists / broadcasts (`ToCount > 10`, noreply/listserv senders)

Do not pad the report. Quiet periods should be reported as quiet.

### Response-time flags (compute before writing)

For every Tier 1/2 inbox email where Antonio is in To:
1. Search Sent Items for a reply in the same `ConversationTopic`
2. **No reply AND email age â‰¥ `UnrepliedThreshold` days** â†’ flag as unreplied
   - For daily (threshold = 0): flag ALL unreplied Tier 1 inbox items, no age gate
3. **Reply exists AND gap â‰¥ `SlowThreshold` days** â†’ flag as slow reply
4. Collect all flags for the Response-Time Flags section only â€” do not mention response time elsewhere.

### MSF country inference (MSF addresses only)

From Tier 1/2 inbox, identify `FromEmail` containing `msf.org` or `msf.` + country TLD:
- Subdomain: `@[country].msf.org` â†’ country
- Country-code TLD: `@msf.cd`, `@msf.ke` â†’ country
- Display name containing a country or mission abbreviation

Exclude all non-MSF addresses. Group unresolvable under "MSF â€“ Origin Unclear".

---

## Step 3.5 â€” Merge actions into the task ledger

Extract candidate actions from Tier 1/2 threads, reconcile against `tasks.json`.

### Stable IDs

```powershell
function Get-TaskKeys {
    param([string]$Topic, [string]$FromEmail, [string]$Action)
    $sha  = [System.Security.Cryptography.SHA1]::Create()
    $norm = { param($s) (($s + "").ToLower().Trim() -replace '\s+', ' ') }
    $skIn = (& $norm $Topic) + "|" + (& $norm $FromEmail)
    $sk   = (($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($skIn)) |
              ForEach-Object { $_.ToString("x2") }) -join "").Substring(0, 6)
    $slug = ((& $norm $Action) -replace '[^a-z0-9 ]', '' -replace '\s+', '-')
    $idIn = $sk + "|" + $slug
    $id   = (($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($idIn)) |
              ForEach-Object { $_.ToString("x2") }) -join "").Substring(0, 10)
    [PSCustomObject]@{ source_key = $sk; id = $id }
}
```

`source_key` = hash(topic + from_email) â€” survives action rephrasing within a thread.
`id` = hash(source_key + action slug) â€” frozen on creation, never recomputed.

### Candidate types

`type` âˆˆ { commitment, request, deadline, followup, fyi }
- **commitment** â€” something Antonio said he'd do (from Sent Items)
- **request** â€” something someone asked him to do, not yet done
- **deadline** â€” a dated obligation
- **followup** â€” awaiting reply / needs chasing
- Set `urgent: true` only for genuinely time-sensitive items

### Reconcile

```
for each candidate C:
    keys = Get-TaskKeys(C.topic, C.from_email, C.action)
    pool = existing tasks where source_key == keys.source_key
    match = best semantic match in pool (high bar; same thread only)
    if match:
        reuse match.id and match.source_key
        PRESERVE match.status, match.comments, match.resolution, user-set match.urgent
        refresh match.source (latest subject/person/date); set last_seen = today
        if match.status == "open" AND Sent Items shows it was actioned:
            add a comment "Looks done â€” [evidence]. Confirm in dashboard."
            do NOT set status = "done"
    else:
        create new: id, source_key, status="open",
                    first_seen = last_seen = today, comments=[], resolved_on=null

# Open tasks whose thread did NOT appear this period:
#   leave status and last_seen untouched â†’ renders as carryover/aging
```

**Three invariants â€” never violate:**
1. The review never sets `status = "done"`. Only the user does that in the dashboard.
2. `id` and user-owned fields (`status`, `comments`, `resolution`, `urgent`) are preserve-only.
3. Semantic matching is scoped to one `source_key` â€” keep the bar high.

---

## Step 4 â€” Write the sitrep

The report structure varies by mode. Use **first-person professional tone**, real names and
project names. Keep every entry tight â€” one thread = one entry.

---

### DAILY MODE (DaysBack = 1)

Header: **Daily Sitrep â€” [Date]**
Stat line: [N] emails ([inbox] received Â· [sent] sent) Â· [M] meetings Â· Generated [time]

#### Summary
1â€“2 sentences. Volume, tone, one standout item. "Quiet" is a valid answer.

#### Priority Inbox
*New Tier 1 items today that require a response or action â€” ordered by urgency.*

For each item: subject, sender, what was asked/raised, whether a reply was sent.
Mark items with no reply sent as `âš  Awaiting response`.

```html
<section>
  <h2>Priority Inbox</h2>
  <div class="entry">
    <div class="subject">[SUBJECT]</div>
    <div class="meta">From [PERSON] Â· [TIME]</div>
    <div class="detail">[WHAT WAS ASKED OR RAISED]</div>
    <div class="response"><span class="label">Response:</span> [REPLY / âš  Awaiting response]</div>
  </div>
</section>
```

#### What I Sent Today
*From Sent Items â€” outputs, decisions, coordination. Skip automated sends and calendar acceptances.*

Group by workstream if â‰¥ 3 sent items; otherwise list individually.

#### Meetings
Accepted and organised today.

| Time | Meeting | Role | Duration |
|---|---|---|---|

If none: "No meetings today."

#### Coming Up â€” [Tomorrow's date or "Next N days"]
*Calendar events and known deadlines in the next [LookForwardDays] day(s).*

**Calendar:**

| Date/Time | Meeting | Role | Duration |
|---|---|---|---|

**Upcoming deadlines from open tasks:**
List any open tasks in the ledger with `urgent = true` or `source.date` within the look-forward window.

If nothing upcoming: "Nothing scheduled in the next [N] day(s)."

#### Response-Time Flags
*Tier 1 direct emails today with no reply sent.*

- âš  **[Subject]** â€” from [Person] ([time received]) â€” no reply sent

If none: omit section.

#### Carryover
*Open tasks from previous days â€” driven by the ledger, not re-derived.*

- â†© [Action] â€” since [first_seen] (âš  if `urgent = true` or age â‰¥ 14 days)
- ~âœ“ [Action] â€” looks done: [evidence] â€” confirm in dashboard
- âœ“ [Action] â€” resolved [resolution] (if status = done this run)

#### New Actions Today
*Tasks first_seen = today.*

- [ ] **[Action]** âš  â€” re: "[Subject]" Â· [Person] Â· [time]

#### Key Contacts
Name â€” one-line context.

---

### WEEKLY / CUSTOM MODE (DaysBack â‰¥ 2)

Header: **[PeriodLabel] Sitrep â€” [PeriodStart] to [PeriodEnd]**
Stat line: [N] emails ([inbox] received Â· [sent] sent) Â· [M] meetings Â· Generated [time]

#### Summary
2â€“3 sentences. Volume, main focus areas, pressure points or wins.

#### What I Did This [Period]
*From Sent Items â€” decisions, outputs, coordination grouped by workstream.*
Skip automated sends, calendar acceptances, brief acknowledgements (unless they close something important).

#### Meetings
Accepted and organised. Table: Date | Meeting | Role | Duration.

#### Requests & Interactions
*Tier 1 and Tier 2 inbox â€” direct requests and meaningful exchanges.*
Group related back-and-forth as single entries.

#### MSF Country Engagement
*MSF addresses only.* Group by inferred country. Omit if none.

#### Response-Time Flags
*Slow replies (â‰¥ `SlowThreshold` days) and unreplied direct emails (â‰¥ `UnrepliedThreshold` days old).*
Omit if none.

#### Workflow Insights
*Factual observations from email metadata. 3â€“5 bullets max. No interpretation beyond what the data shows.*
Examples: volume vs prior period, To vs CC ratio, time-of-day pattern, weekend activity, spike in a workstream.

#### Coming Up â€” Next [LookForwardDays] Day(s)
*Calendar events and known deadlines in the next [LookForwardDays] days.*

**Calendar:**

| Date | Meeting | Role | Duration |
|---|---|---|---|

**Upcoming deadlines from open tasks:**
List tasks.json items with `urgent = true`, or items whose `source.date` or context suggests a near-term deadline.

If nothing: "Nothing scheduled in the next [N] days."

#### Carryover from Previous Period(s)
*Open tasks with `first_seen` before this period's start â€” driven by the ledger.*
- `status = done` â†’ âœ“ with resolution
- still open â†’ â†© with age; flag â‰¥14 days as aging
- looks-done suggestion â†’ ~âœ“ with evidence; confirm in dashboard

Omit section if the ledger has no pre-existing tasks.

#### Still Open / Pending Action
*New tasks created this run (first_seen within this period).*

- [ ] **[Action]** âš  â€” re: "[Subject]" Â· [Person] Â· [Date]

#### Key Contacts This [Period]
Name â€” one-line context each.

#### Documents & Attachments
Omit if none.

---

## Step 5 â€” Save the ledger, then the styled HTML, then report.json

### 5a â€” Save tasks.json (UTF-8 no BOM, atomic)

```powershell
$dir = if ($env:REVIEW_EMAILS_DIR) { $env:REVIEW_EMAILS_DIR } else { "$env:USERPROFILE\Downloads\Weekly report" }
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force $dir | Out-Null }
$tasksPath = "$dir\tasks.json"

$ledger = @{ version = 1; updated = (Get-Date).ToString("o"); tasks = $allTasks }
$json   = $ledger | ConvertTo-Json -Depth 12
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
if (Test-Path $tasksPath) { Copy-Item $tasksPath "$tasksPath.bak" -Force }
$tmp = "$tasksPath.tmp"
[System.IO.File]::WriteAllText($tmp, $json, $utf8NoBom)
Move-Item $tmp $tasksPath -Force
```

### 5b â€” Save the HTML sitrep

```powershell
$filename = "$dir\$(Get-Date -Format 'yyyy-MM-dd')_$($FileSuffix)-sitrep.html"
[System.IO.File]::WriteAllText($filename, $htmlContent, $utf8NoBom)
```

### 5c â€” Save report.json (dashboard live view, overwrite each run)

Schema â€” mirror the HTML exactly. Arrays may be empty, never null.

```jsonc
{
  "version": 1,
  "period": {
    "type":      "daily",          // "daily" | "weekly" | "custom"
    "days":      1,                // DaysBack
    "start":     "22 Jun 2026",
    "end":       "22 Jun 2026",
    "generated": "22 Jun 2026 12:00"
  },
  "stats": {
    "emails": 32, "received": 28, "sent": 4,
    "meetings": 3, "capped": false, "filtered": 11
  },
  "summary": "...",
  // Daily mode fields:
  "priority_inbox": [ { "subject": "...", "meta": "From X Â· 09:15", "detail": "...", "response": "...", "noreply": true } ],
  "sent_today":     [ { "workstream": "...", "detail": "..." } ],
  // Weekly/custom mode fields:
  "workstreams":    [ { "title": "...", "detail": "..." } ],
  "interactions":   [ { "subject": "...", "meta": "...", "detail": "...", "response": "...", "noreply": false } ],
  "countries":      [ { "name": "...", "inferred": "...", "items": ["..."] } ],
  // Shared fields:
  "meetings":       [ { "date": "22 Jun", "time": "09:00", "subject": "...", "role": "Accepted", "duration": 60 } ],
  "coming_up":      [ { "date": "23 Jun", "time": "10:00", "subject": "...", "role": "Not responded", "duration": 30, "organizer": "..." } ],  // role = true OlResponseStatus from Step 2b (Organiser/Accepted/Tentative/Not responded) â€” never default to Accepted
  "coming_up_tasks": [ { "action": "...", "urgency": "urgent", "due_hint": "tomorrow" } ],
  "flags":          [ { "subject": "...", "person": "...", "detail": "22 Jun Â· no reply sent" } ],
  "insights":       [ "..." ],
  "contacts":       [ { "name": "...", "context": "..." } ],
  "attachments":    [ { "subject": "...", "meta": "Person Â· Date" } ]
}
```

```powershell
$rjson = $report | ConvertTo-Json -Depth 12
$reportPath = "$dir\report.json"
[System.IO.File]::WriteAllText("$reportPath.tmp", $rjson, $utf8NoBom)
Move-Item "$reportPath.tmp" $reportPath -Force
```

Confirm saved paths and remind: live dashboard at `start-dashboard.ps1` â†’ http://127.0.0.1:8787

---

## HTML template (shared; adapt section order and labels per mode)

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>[PeriodLabel] Sitrep [PERIOD_DATE_OR_RANGE]</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 14px;
         color: #1a1a1a; background: #fff; max-width: 880px; margin: 40px auto; padding: 0 24px 60px; }
  header { border-bottom: 3px solid #c0392b; padding-bottom: 16px; margin-bottom: 28px; }
  header h1 { font-size: 20px; font-weight: 700; color: #c0392b; letter-spacing: 0.04em; text-transform: uppercase; }
  header .meta { font-size: 12px; color: #888; margin-top: 5px; line-height: 1.6; }
  .summary-box { background: #f9f9f9; border-left: 4px solid #c0392b; padding: 14px 18px;
                 margin-bottom: 32px; font-size: 14px; line-height: 1.7; color: #333; }
  section { margin-bottom: 34px; }
  section h2 { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;
               color: #c0392b; border-bottom: 1px solid #eee; padding-bottom: 6px; margin-bottom: 14px; }
  .entry { margin-bottom: 14px; padding-bottom: 14px; border-bottom: 1px solid #f0f0f0; }
  .entry:last-child { border-bottom: none; }
  .entry .subject { font-weight: 600; font-size: 14px; color: #1a1a1a; margin-bottom: 3px; }
  .entry .meta { font-size: 12px; color: #888; margin-bottom: 5px; }
  .entry .detail { font-size: 13px; color: #444; line-height: 1.6; }
  .entry .response { font-size: 13px; color: #555; margin-top: 4px; }
  .entry .response .label { font-weight: 600; color: #1a1a1a; }
  .no-reply { color: #c0392b; font-weight: 600; font-size: 12px; margin-top: 4px; }
  .mtg-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 4px; }
  .mtg-table th { text-align: left; font-size: 11px; font-weight: 600; color: #888;
                  text-transform: uppercase; letter-spacing: 0.05em; padding: 4px 8px 6px;
                  border-bottom: 1px solid #eee; }
  .mtg-table td { padding: 7px 8px; border-bottom: 1px solid #f5f5f5; vertical-align: top; color: #333; }
  .mtg-table td.role-org { color: #c0392b; font-weight: 600; }
  .mtg-table td.role-acc { color: #555; }
  .mtg-table td.role-pending { color: #b9770e; font-weight: 600; } /* Not responded / Tentative â€” needs an RSVP */
  /* Coming Up */
  .upcoming-box { background: #f3f8ff; border-left: 4px solid #2980b9; padding: 12px 16px;
                  margin-bottom: 10px; font-size: 13px; color: #333; border-radius: 2px; }
  .upcoming-box .upheading { font-weight: 700; font-size: 12px; color: #2980b9;
                              text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
  .upcoming-box .deadline-list { list-style: none; margin-top: 8px; }
  .upcoming-box .deadline-list li { padding: 4px 0; font-size: 13px; color: #555;
                                    border-bottom: 1px solid #dde8f5; }
  .upcoming-box .deadline-list li:last-child { border-bottom: none; }
  .upcoming-box .deadline-list li .dl-label { font-weight: 600; color: #c0392b; margin-right: 6px; }
  /* Country engagement */
  .country-block { margin-bottom: 14px; }
  .country-block .country-name { font-weight: 700; font-size: 13px; color: #1a1a1a; margin-bottom: 4px; }
  .country-block .country-name .inferred { font-weight: 400; font-size: 11px; color: #aaa; margin-left: 6px; }
  .country-block ul { padding-left: 16px; font-size: 13px; color: #444; line-height: 1.6; }
  /* Response flags */
  .flag-list { list-style: none; }
  .flag-list li { display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px;
                  font-size: 13px; line-height: 1.5; }
  .flag-list li .warn { color: #c0392b; font-size: 14px; flex-shrink: 0; }
  .flag-list li .flag-subject { font-weight: 600; }
  .flag-list li .flag-detail { color: #888; font-size: 12px; }
  /* Workflow insights */
  .insights-list { list-style: none; }
  .insights-list li { padding: 6px 0 6px 14px; border-bottom: 1px solid #f5f5f5;
                      font-size: 13px; color: #444; line-height: 1.5; position: relative; }
  .insights-list li::before { content: "â€“"; position: absolute; left: 0; color: #c0392b; }
  /* Pending / carryover */
  .pending-list { list-style: none; }
  .pending-list li { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px;
                     font-size: 13px; line-height: 1.5; }
  .pending-list li input[type=checkbox] { margin-top: 2px; flex-shrink: 0; accent-color: #c0392b; }
  .pending-list li .source { color: #999; font-size: 12px; }
  .pending-list li.urgent .text { color: #c0392b; font-weight: 600; }
  .carryover-list { list-style: none; }
  .carryover-list li { margin-bottom: 8px; font-size: 13px; line-height: 1.5;
                       padding-left: 20px; position: relative; color: #444; }
  .carryover-list li::before { content: "â†©"; position: absolute; left: 0; color: #c0392b; }
  .carryover-list li.resolved::before { content: "âœ“"; color: #27ae60; }
  .carryover-list li.resolved { color: #aaa; text-decoration: line-through; }
  .carryover-list li.looks-done::before { content: "~âœ“"; color: #e67e22; font-size: 11px; }
  .carryover-list li.looks-done { color: #888; }
  .carryover-list li.aging { color: #c0392b; }
  /* Contacts */
  .contacts-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .contacts-table td { padding: 6px 10px; border-bottom: 1px solid #f0f0f0; vertical-align: top; }
  .contacts-table td:first-child { font-weight: 600; width: 28%; }
  /* Attachments */
  .attach-list { list-style: none; font-size: 13px; }
  .attach-list li { padding: 5px 0; border-bottom: 1px solid #f5f5f5; color: #444; }
  .attach-list li .subject { font-weight: 600; }
  .attach-list li .meta { color: #999; margin-left: 8px; }
  .empty { color: #bbb; font-style: italic; font-size: 13px; }
</style>
</head>
<body>

<header>
  <h1>[PERIOD_LABEL] Sitrep</h1>
  <div class="meta">
    [PERIOD_DATE_OR_RANGE]&nbsp;&nbsp;Â·&nbsp;&nbsp;Generated [GENERATED_AT]<br>
    [TOTAL] emails ([INBOX] received Â· [SENT] sent)&nbsp;&nbsp;Â·&nbsp;&nbsp;[MEETINGS] meetings
  </div>
</header>

<div class="summary-box">[SUMMARY]</div>

<!-- DAILY: Priority Inbox | WEEKLY: What I Did -->
<section>
  <h2>Priority Inbox</h2><!-- daily: "Priority Inbox" | weekly: "What I Did This [Period]" -->
  <div class="entry">
    <div class="subject">[SUBJECT]</div>
    <div class="meta">From [PERSON] Â· [TIME/DATE]</div>
    <div class="detail">[WHAT WAS ASKED]</div>
    <div class="response"><span class="label">Response:</span> [REPLY OR âš  Awaiting response]</div>
    <!-- <div class="no-reply">âš  No reply sent</div> -->
  </div>
</section>

<!-- MEETINGS -->
<section>
  <h2>Meetings</h2>
  <table class="mtg-table">
    <tr><th>Date</th><th>Meeting</th><th>Role</th><th>Duration</th></tr>
    <tr><td>[DATE]</td><td>[SUBJECT]</td><td class="role-org">Organiser</td><td>[X] min</td></tr>
    <tr><td>[DATE]</td><td>[SUBJECT]</td><td class="role-acc">Accepted</td><td>[X] min</td></tr>
  </table>
  <!-- If none: <p class="empty">No meetings [today / this period].</p> -->
</section>

<!-- COMING UP -->
<section>
  <h2>Coming Up â€” [NEXT_PERIOD_LABEL]</h2>
  <div class="upcoming-box">
    <div class="upheading">Calendar</div>
    <table class="mtg-table">
      <tr><th>Date / Time</th><th>Meeting</th><th>Role</th><th>Duration</th></tr>
      <!-- Render [ROLE] verbatim from the Step 2b `Role` field â€” never hardcode "Accepted".
           Class by status: Organiserâ†’role-org Â· Acceptedâ†’role-acc Â· Not responded/Tentativeâ†’role-pending (action needed). -->
      <tr><td>[DATE TIME]</td><td>[SUBJECT]</td><td class="[ROLE_CLASS]">[ROLE]</td><td>[X] min</td></tr>
    </table>
    <div class="upheading" style="margin-top:12px">Upcoming task deadlines</div>
    <ul class="deadline-list">
      <li><span class="dl-label">âš </span>[ACTION] â€” [context / due hint]</li>
    </ul>
  </div>
  <!-- If nothing: <p class="empty">Nothing scheduled in the next [N] day(s).</p> -->
</section>

<!-- RESPONSE-TIME FLAGS -->
<section>
  <h2>Response-Time Flags</h2>
  <ul class="flag-list">
    <li>
      <span class="warn">âš </span>
      <div>
        <span class="flag-subject">[SUBJECT]</span> â€” from [PERSON]
        <span class="flag-detail">([DATE/TIME] Â· no reply sent)</span>
      </div>
    </li>
  </ul>
  <!-- If none: <p class="empty">No response-time issues.</p> -->
</section>

<!-- WEEKLY ONLY: MSF Country Engagement -->
<section>
  <h2>MSF Country Engagement</h2>
  <div class="country-block">
    <div class="country-name">[COUNTRY] <span class="inferred">(inferred)</span></div>
    <ul><li>[WHAT WAS EXCHANGED]</li></ul>
  </div>
</section>

<!-- WEEKLY ONLY: Workflow Insights -->
<section>
  <h2>Workflow Insights</h2>
  <ul class="insights-list">
    <li>[INSIGHT]</li>
  </ul>
</section>

<!-- CARRYOVER -->
<section>
  <h2>Carryover</h2><!-- daily: "Carryover" | weekly: "Carryover from Previous [Period]" -->
  <ul class="carryover-list">
    <li class="resolved">[ITEM] <span style="color:#aaa;font-size:12px">â€” resolved: [HOW]</span></li>
    <li class="looks-done">[ITEM] <span style="color:#e67e22;font-size:12px">â€” looks done â€” confirm in dashboard</span></li>
    <li class="aging">[ITEM] <span style="color:#c0392b;font-size:12px">â€” since [DATE] (AGING)</span></li>
    <li>[ITEM] <span style="color:#aaa;font-size:12px">â€” since [DATE]</span></li>
  </ul>
</section>

<!-- NEW ACTIONS -->
<section>
  <h2>New Actions [Today / This Period]</h2>
  <ul class="pending-list">
    <li class="urgent">
      <input type="checkbox">
      <div><span class="text">[ACTION] âš </span><br>
      <span class="source">Re: "[SUBJECT]" Â· [PERSON] Â· [DATE]</span></div>
    </li>
    <li>
      <input type="checkbox">
      <div><span class="text">[ACTION]</span><br>
      <span class="source">Re: "[SUBJECT]" Â· [PERSON] Â· [DATE]</span></div>
    </li>
  </ul>
</section>

<!-- KEY CONTACTS -->
<section>
  <h2>Key Contacts</h2>
  <table class="contacts-table">
    <tr><td>[NAME]</td><td>[CONTEXT]</td></tr>
  </table>
</section>

<!-- ATTACHMENTS (weekly/custom only if relevant) -->
<section>
  <h2>Documents &amp; Attachments</h2>
  <ul class="attach-list">
    <li><span class="subject">[SUBJECT]</span><span class="meta">[PERSON] Â· [DATE]</span></li>
  </ul>
  <!-- If none: <p class="empty">None.</p> -->
</section>

</body>
</html>
```

---

## Edge cases

- **SentCount = 0**: Warn â€” Outlook may store sent mail in a non-default folder.
- **MeetingCount = 0 unexpectedly**: `IncludeRecurrences` must be set before `Sort`; if still 0, ask user to verify calendar sync.
- **Upcoming calendar query returns 0 items**: Report "Nothing on the calendar for the next [N] day(s)" â€” do not skip the section.
- **Context too large**: Rerun with `-MaxEmails 100 -MaxBodyLength 200`; note truncation in report header.
- **All emails Tier 3**: Report plainly â€” do not pad.
- **MSF country unresolvable**: Group under "MSF â€“ Origin Unclear"; do not guess.
- **Confidential field content**: Summarise thematically; do not reproduce beneficiary or security details verbatim.
- **Daily run with zero emails**: Report volume as zero and note if Outlook was likely closed. Carryover and Coming Up sections still render from ledger + calendar.
