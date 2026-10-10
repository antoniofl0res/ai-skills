# Extraction Playbook: TikTok Profile and Video Data

How to get an authoritative dataset from any public TikTok profile using the controlled browser. Every obstacle below was hit in production; every fix below worked.

## Why the obvious approaches fail

| Approach | Result |
|---|---|
| WebFetch / reader tools on the profile URL | At best the header stats (followers, likes, bio). Video grid is JavaScript-rendered; never captured. |
| Search engines for the account | Small accounts are not indexed. |
| Direct `fetch()` of `/api/post/item_list/` | HTTP 200 with an **empty body**. TikTok requires a per-request signature (X-Bogus family). You cannot construct it; stop trying variants. |
| Reading videos from the DOM snapshot | The grid lazy-loads, sometimes renders "Something went wrong", and holds no metrics until each video is opened. Dead end for bulk inventory. |

The reliable path: let TikTok's own page JavaScript make the signed request, and intercept the response.

## Step-by-step

### 1. Open the profile

Follow the `browser-use:control-browser` skill: bootstrap the browser runtime, create a tab, `goto` the profile URL, wait for `domcontentloaded`, then a fixed `waitForTimeout` of roughly 5,000 ms (TikTok hydrates late).

Expect these obstacles, in any combination:

- **Login modal** covering the page. It has a Skip button. If a locator click times out, re-snapshot and click page-side: find the `[role="dialog"]` containing a button whose text is "Skip" and call `.click()` on it from `evaluate`.
- **Video grid error state**: main region shows "Something went wrong" plus a Refresh button. Good news: that Refresh button triggers exactly the signed `item_list` request you want to capture.
- **Cookie/consent walls**: dismiss with their explicit accept/skip control; never accept-with-enter on a modal you have not read.

### 2. Read the profile header from embedded state

TikTok embeds server-rendered JSON in a script tag. Read it from the page context:

```js
const profile = await tab.playwright.evaluate(`(() => {
  const el = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__');
  if (!el) return { found: false };
  const scope = JSON.parse(el.textContent)['__DEFAULT_SCOPE__'];
  const ud = scope && scope['webapp.user-detail'];
  if (!ud || !ud.userInfo) return { found: false, scopes: scope ? Object.keys(scope) : [] };
  const u = ud.userInfo.user || {};
  const s = ud.userInfo.stats || {};
  return {
    found: true,
    uniqueId: u.uniqueId, nickname: u.nickname, signature: u.signature,
    verified: u.verified, privateAccount: u.privateAccount,
    language: u.language, secUid: u.secUid, id: u.id,
    followerCount: s.followerCount, followingCount: s.followingCount,
    heartCount: s.heartCount, videoCount: s.videoCount
  };
})()`);
```

Notes:

- `secUid` and `videoCount` are load-bearing: the first identifies the account internally, the second is your completeness check.
- The scope name (`webapp.user-detail`) and container id are stable as of October 2026; if missing, the returned scope list tells you what to inspect instead.
- The video list is deliberately NOT in this payload. Do not go hunting for it here.

If `privateAccount` is true, stop: report the header stats and state that the inventory is unavailable for private accounts.

### 3. Install the interceptor, then make the page call the API for you

Order matters: interceptor first, trigger second. The page uses both `fetch` and `XMLHttpRequest`, so hook both:

```js
await tab.playwright.evaluate(`(() => {
  if (window.__capturedInstalled) return 'already';
  window.__captured = [];
  const origFetch = window.fetch;
  window.fetch = async function(...args) {
    const resp = await origFetch.apply(this, args);
    try {
      const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
      if (url.includes('item_list')) {
        const clone = resp.clone();
        window.__captured.push({ url, status: resp.status, body: await clone.text() });
      }
    } catch (e) {}
    return resp;
  };
  const origOpen = XMLHttpRequest.prototype.open;
  const origSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    this.__url = url;
    return origOpen.apply(this, [method, url, ...rest]);
  };
  XMLHttpRequest.prototype.send = function(...args) {
    if (this.__url && String(this.__url).includes('item_list')) {
      this.addEventListener('load', () => {
        try { window.__captured.push({ url: String(this.__url), status: this.status, body: this.responseText }); } catch (e) {}
      });
    }
    return origSend.apply(this, args);
  };
  window.__capturedInstalled = true;
  return 'installed';
})()`);
```

The interceptor is read-only by design: it clones responses and stores them on `window.__captured`; it never modifies, replays, or forges requests.

Trigger options, in order of preference:

1. **Grid Refresh button** (if the grid shows the error state): find the button by visible text "Refresh" via `evaluate` and click it.
2. **Reload the tab** (`tab.reload()`), which works but requires reinstalling the interceptor after navigation; prefer the in-page trigger.

Wait 3-6 seconds, then read `window.__captured`. A healthy capture is one entry with status 200 and a body of tens-to-hundreds of KB.

### 4. Parse the captured response

```js
const data = await tab.playwright.evaluate(`(() => {
  const c = window.__captured[0];
  if (!c) return { error: 'nothing captured' };
  let j = null;
  try { j = JSON.parse(c.body); } catch (e) { return { error: 'unparseable body' }; }
  if (!j.itemList) return { error: 'no itemList', keys: Object.keys(j) };
  return {
    count: j.itemList.length, hasMore: j.hasMore, cursor: j.cursor,
    videos: j.itemList.map(v => ({
      id: v.id, desc: v.desc || '', createTime: v.createTime,
      plays: v.stats && v.stats.playCount,
      likes: v.stats && v.stats.diggCount,
      comments: v.stats && v.stats.commentCount,
      shares: v.stats && v.stats.shareCount,
      saves: v.stats && v.stats.collectCount,
      durationSec: v.video && Math.round(v.video.duration),
      musicTitle: v.music && v.music.title,
      musicOriginal: v.music && !!v.music.original
    }))
  };
})()`);
```

Field map (TikTok internal names → meaning): `diggCount` = likes, `collectCount` = saves/favorites, `createTime` = epoch seconds UTC, `stats.playCount` = views. Video URL pattern: `https://www.tiktok.com/@<handle>/video/<id>`.

Pagination: if `hasMore` is true, capture repeats with the returned `cursor` (the page issues the next call as it scrolls; scroll and capture again). Small accounts typically return everything in one response with `hasMore: false`.

### 5. Timestamp the snapshot and run integrity checks

```js
const snapEpoch = await tab.playwright.evaluate('Date.now() / 1000');
```

Then verify, in this order:

1. `count === videoCount` from the profile header (accounting for pagination). Mismatch means incomplete capture; re-trigger.
2. `sum(likes across videos) === heartCount` from the header. Exact match expected on healthy accounts (divergence can indicate removed videos or hidden likes; investigate before trusting either side, and note it in the report if unresolved).
3. Every video has non-null plays/likes/comments/shares/saves and a `createTime`. Nulls mean parse drift; fix the parser, do not fill in values.

## Degradation ladder

If browser capture is impossible in the session, fall back in this order and say which rung you stopped at in the report's limitations:

1. Full pipeline (browser + interceptor): complete inventory.
2. Reader-tool header stats only: profile-level analysis with no per-video data.
3. Nothing extracted: say so; do not publish estimated numbers under any circumstances.
