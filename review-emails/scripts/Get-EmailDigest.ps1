<#
.SYNOPSIS
    Exports emails and calendar meetings from Outlook for the past N*26 hours using the COM API.
    No OAuth, no external connections. Outlook must be installed (need not be open).

.PARAMETER DaysBack
    Logical "days" back to look; each day = 26 hours for buffer (default: 7)

.PARAMETER MaxBodyLength
    Max characters to keep from each email body (default: 600)

.PARAMETER MaxEmails
    Hard cap on total emails exported per folder; inbox and sent are capped independently (default: 300)

.PARAMETER IncludeSent
    Include Sent Items in addition to Inbox (default: true)

.PARAMETER IncludeCalendar
    Include accepted and organised calendar meetings (default: true)

.PARAMETER FilterNoise
    Skip broadcast / distribution-list mail (Google Groups, newsletters, mailing
    lists, no-reply marketing blasts) in the Inbox BEFORE it counts against
    -MaxEmails, so the cap budget is spent on real correspondence. SharePoint /
    Teams / Planner collaboration notifications are deliberately KEPT. Sent Items
    are never filtered. (default: true)

.PARAMETER ExtraNoisePatterns
    Additional case-insensitive substrings to treat as noise senders, e.g.
    @('somelist.example.org','newsletter@vendor.com'). Appended to the built-in list.
#>
param(
    [int]$DaysBack = 7,
    [int]$MaxBodyLength = 600,
    [int]$MaxEmails = 300,
    [bool]$IncludeSent = $true,
    [bool]$IncludeCalendar = $true,
    [bool]$FilterNoise = $true,
    [string[]]$ExtraNoisePatterns = @(),
    [int]$NextDays = 1
)

$ErrorActionPreference = "Stop"

# --- Noise classification (Inbox only) ---------------------------------------
# Senders matching any of these substrings are broadcast/list traffic, not direct
# correspondence. Matched BEFORE the -MaxEmails cap so they never crowd out real mail.
$NoiseDomains = @(
    'googlegroups.com','listserv','mailman','sympa',                 # mailing lists
    'mailchimp','mcsv.net','mcdlv.net','mailchimpapp.net','cmail',    # ESP / marketing
    'sendgrid','mailgun','constantcontact','exacttarget','campaign-archive',
    'quarantine@messaging.microsoft.com','bamboohr.com',             # automated digests
    'uber.com','flyairlink.com','noreply@uber','receipts@',          # receipts / travel noise
    'campaign.who.int','saafrica.org','isid.org','scilit.com'        # newsletters seen in practice
) + $ExtraNoisePatterns

# Collaboration notifications to ALWAYS KEEP even though they look automated.
$CollabAllow = @('sharepointonline.com','sharepoint.com','teams.mail.microsoft','planner.office.com')

function Test-Noise([string]$from, [string]$body) {
    $f = ($from + "").ToLower()
    if ($f) {
        foreach ($a in $CollabAllow) { if ($f.Contains($a)) { return $false } }
        foreach ($d in $NoiseDomains) { if ($d -and $f.Contains($d.ToLower())) { return $true } }
    }
    # Generic newsletter footer signals — catches novel senders. Collab mail already
    # returned $false above, so its "manage notifications" footer won't trip this.
    $b = ($body + "").ToLower()
    if ($b.Contains('unsubscribe') -or $b.Contains('you are receiving this') -or
        $b.Contains('manage your subscription') -or $b.Contains('view this email in your browser') -or
        $b.Contains('update your preferences')) { return $true }
    return $false
}

$inboxFiltered    = 0
$filteredBySender = @{}
# Each logical "day" = 26 hours to ensure no edge-of-day gaps
$cutoffDate  = (Get-Date).AddHours(-($DaysBack * 26))
$cutoffStr   = $cutoffDate.ToString("MM/dd/yyyy HH:mm")
$periodEnd   = (Get-Date).ToString("MM/dd/yyyy 23:59")
$inboxEmails = [System.Collections.Generic.List[hashtable]]::new()
$sentEmails  = [System.Collections.Generic.List[hashtable]]::new()
$meetings    = [System.Collections.Generic.List[hashtable]]::new()
$upcoming    = [System.Collections.Generic.List[hashtable]]::new()

# OlResponseStatus -> human label. CRITICAL for the forward "Coming Up" view:
# an invite sitting on the calendar is NOT necessarily accepted. Never assume.
#   0 None · 1 Organised · 2 Tentative · 3 Accepted · 4 Declined · 5 NotResponded
$ResponseLabel = @{
    0 = "Not responded"; 1 = "Organiser"; 2 = "Tentative"
    3 = "Accepted";      4 = "Declined";  5 = "Not responded"
}

function Sanitize-Body([string]$raw) {
    $clean = $raw -replace "`r`n", " " -replace "`n", " " -replace "\s{3,}", "  "
    $clean = $clean.Trim()
    if ($clean.Length -gt $MaxBodyLength) {
        return $clean.Substring(0, $MaxBodyLength) + " [...]"
    }
    return $clean
}

try {
    $outlook   = New-Object -ComObject Outlook.Application
    $namespace = $outlook.GetNamespace("MAPI")
} catch {
    Write-Error "Could not connect to Outlook COM. Is Outlook installed? Error: $_"
    exit 1
}

# --- INBOX ---
$inbox = $namespace.GetDefaultFolder(6)
try {
    $inboxItems = $inbox.Items
    $inboxItems.Sort("[ReceivedTime]", $true)
    $filtered = $inboxItems.Restrict("[ReceivedTime] >= '$cutoffStr'")

    foreach ($item in $filtered) {
        if ($inboxEmails.Count -ge $MaxEmails) { break }
        if ($item.Class -ne 43) { continue }

        if ($FilterNoise -and (Test-Noise "$($item.SenderEmailAddress)" "$($item.Body)")) {
            $inboxFiltered++
            $key = "$($item.SenderEmailAddress)"; if (-not $key) { $key = "$($item.SenderName)" }
            if ($filteredBySender.ContainsKey($key)) { $filteredBySender[$key]++ } else { $filteredBySender[$key] = 1 }
            continue
        }

        $toField = "$($item.To)"
        $ccField = "$($item.CC)"
        $toCount = if ($toField) { ($toField -split ";").Count } else { 0 }
        $ccCount = if ($ccField) { ($ccField -split ";").Count } else { 0 }

        $inboxEmails.Add(@{
            Subject           = "$($item.Subject)"
            From              = "$($item.SenderName)"
            FromEmail         = "$($item.SenderEmailAddress)"
            To                = $toField
            CC                = $ccField
            ToCount           = $toCount
            CCCount           = $ccCount
            Date              = $item.ReceivedTime.ToString("yyyy-MM-dd HH:mm")
            Folder            = "Inbox"
            Body              = Sanitize-Body $item.Body
            HasAttachments    = ($item.Attachments.Count -gt 0)
            ConversationTopic = "$($item.ConversationTopic)"
            Importance        = [int]$item.Importance
        })
    }
} catch {
    Write-Warning "Error reading Inbox: $_"
}

# --- SENT ITEMS ---
# Restrict on SentOn is unreliable; iterate sorted descending and break at cutoff
if ($IncludeSent) {
    $sentFolder = $namespace.GetDefaultFolder(5)
    try {
        $sentItems = $sentFolder.Items
        $sentItems.Sort("[SentOn]", $true)

        foreach ($item in $sentItems) {
            if ($sentEmails.Count -ge $MaxEmails) { break }
            if ($item.Class -ne 43) { continue }

            $sentOn = $null
            try { $sentOn = $item.SentOn } catch { continue }
            if ($null -eq $sentOn) { continue }
            if ($sentOn -lt $cutoffDate) { break }

            $toField = "$($item.To)"
            $ccField = "$($item.CC)"
            $toCount = if ($toField) { ($toField -split ";").Count } else { 0 }
            $ccCount = if ($ccField) { ($ccField -split ";").Count } else { 0 }

            $sentEmails.Add(@{
                Subject           = "$($item.Subject)"
                From              = "Me"
                FromEmail         = ""
                To                = $toField
                CC                = $ccField
                ToCount           = $toCount
                CCCount           = $ccCount
                Date              = $sentOn.ToString("yyyy-MM-dd HH:mm")
                Folder            = "Sent Items"
                Body              = Sanitize-Body $item.Body
                HasAttachments    = ($item.Attachments.Count -gt 0)
                ConversationTopic = "$($item.ConversationTopic)"
                Importance        = [int]$item.Importance
            })
        }
    } catch {
        Write-Warning "Error reading Sent Items: $_"
    }
}

# --- CALENDAR: accepted and organised meetings only ---
# MeetingStatus: 1=Organiser, 3=Received (attendee invite)
# ResponseStatus: 1=Organised, 3=Accepted
if ($IncludeCalendar) {
    $calFolder = $namespace.GetDefaultFolder(9)
    try {
        $calItems = $calFolder.Items
        $calItems.IncludeRecurrences = $true   # must be set before Sort
        $calItems.Sort("[Start]", $false)       # ascending required for recurrence expansion
        $calFilter = "[Start] >= '$cutoffStr' AND [Start] <= '$periodEnd'"
        $calFiltered = $calItems.Restrict($calFilter)

        foreach ($item in $calFiltered) {
            if ($item.Class -ne 26) { continue }  # 26 = olAppointmentItem

            $ms = [int]$item.MeetingStatus
            $rs = [int]$item.ResponseStatus

            # Include if: organiser (ms=1, rs=1) OR accepted attendee (ms=3, rs=3)
            $isOrganiser = ($ms -eq 1 -and $rs -eq 1)
            $isAccepted  = ($ms -eq 3 -and $rs -eq 3)
            if (-not ($isOrganiser -or $isAccepted)) { continue }

            $role = if ($isOrganiser) { "Organiser" } else { "Accepted" }

            $meetings.Add(@{
                Subject   = "$($item.Subject)"
                Start     = $item.Start.ToString("yyyy-MM-dd HH:mm")
                End       = $item.End.ToString("yyyy-MM-dd HH:mm")
                Duration  = [int]$item.Duration   # minutes
                Organizer = "$($item.Organizer)"
                Location  = "$($item.Location)"
                Role      = $role
                Required  = "$($item.RequiredAttendees)"
                Optional  = "$($item.OptionalAttendees)"
            })
        }
    } catch {
        Write-Warning "Error reading Calendar: $_"
    }
}

# --- FORWARD CALENDAR: the "Coming Up" view (next $NextDays days) ---
# Unlike the backward view above (which only emits meetings already accepted/organised),
# this includes EVERY invite on the calendar regardless of response — because the whole
# point of the forward view is to surface invites that still need a decision. Each item
# carries its TRUE ResponseStatus label, so the brief must never relabel these as Accepted.
if ($IncludeCalendar -and $NextDays -gt 0) {
    $fwdStart = (Get-Date).Date.AddDays(1)                       # tomorrow 00:00
    $fwdEnd   = (Get-Date).Date.AddDays($NextDays).AddHours(23).AddMinutes(59)
    $fwdStartStr = $fwdStart.ToString("MM/dd/yyyy HH:mm")
    $fwdEndStr   = $fwdEnd.ToString("MM/dd/yyyy HH:mm")
    try {
        $calFolder2 = $namespace.GetDefaultFolder(9)
        $calItems2  = $calFolder2.Items
        $calItems2.IncludeRecurrences = $true
        $calItems2.Sort("[Start]", $false)
        $fwdFiltered = $calItems2.Restrict("[Start] >= '$fwdStartStr' AND [Start] <= '$fwdEndStr'")

        foreach ($item in $fwdFiltered) {
            if ($item.Class -ne 26) { continue }
            $rs = [int]$item.ResponseStatus
            if ($rs -eq 4) { continue }   # skip meetings the user has declined
            $label = $ResponseLabel[$rs]; if (-not $label) { $label = "Not responded" }

            $upcoming.Add(@{
                Subject   = "$($item.Subject)"
                Start     = $item.Start.ToString("yyyy-MM-dd HH:mm")
                End       = $item.End.ToString("yyyy-MM-dd HH:mm")
                Duration  = [int]$item.Duration
                Organizer = "$($item.Organizer)"
                Location  = "$($item.Location)"
                Role      = $label                 # TRUE response status — do not override
                ResponseStatus = $rs
                Required  = "$($item.RequiredAttendees)"
                Optional  = "$($item.OptionalAttendees)"
            })
        }
    } catch {
        Write-Warning "Error reading forward Calendar: $_"
    }
}

$allEmails = [System.Collections.Generic.List[hashtable]]::new()
foreach ($e in $inboxEmails) { $allEmails.Add($e) }
foreach ($e in $sentEmails)  { $allEmails.Add($e) }

# Top filtered senders (for transparency in the report)
$topFiltered = $filteredBySender.GetEnumerator() |
    Sort-Object Value -Descending | Select-Object -First 10 |
    ForEach-Object { [PSCustomObject]@{ Sender = $_.Key; Count = $_.Value } }

[PSCustomObject]@{
    ExportedAt         = (Get-Date).ToString("yyyy-MM-dd HH:mm")
    PeriodStart        = $cutoffDate.ToString("yyyy-MM-dd HH:mm")
    PeriodEnd          = (Get-Date).ToString("yyyy-MM-dd HH:mm")
    DaysBack           = $DaysBack
    HoursBack          = $DaysBack * 26
    TotalEmails        = $allEmails.Count
    InboxCount         = $inboxEmails.Count
    SentCount          = $sentEmails.Count
    MeetingCount       = $meetings.Count
    NoiseFilterOn      = $FilterNoise
    InboxFilteredCount = $inboxFiltered           # broadcast items skipped before the cap
    InboxCapped        = ($inboxEmails.Count -ge $MaxEmails)  # true only if REAL mail hit the ceiling
    MaxEmails          = $MaxEmails
    TopFilteredSenders = $topFiltered
    Emails             = $allEmails.ToArray()
    Meetings           = $meetings.ToArray()
    Upcoming           = $upcoming.ToArray()
    UpcomingCount      = $upcoming.Count
} | ConvertTo-Json -Depth 5
