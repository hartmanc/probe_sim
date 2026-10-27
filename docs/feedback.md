# The report button: `/api/feedback`

Start menu → **Report a bug / request a feature** (`src/app/feedback.ts`) sends the player's text to `api/feedback.ts`
(Vercel Function), which files a **public GitHub issue** on `hartmanc/probe_sim` (`src/feedback/handler.ts`, tested in
`src/feedback/__tests__/handler.test.ts` with a fake token and a fake GitHub). Owner's decision, 26 Oct 2026.

## What is sent and what the issue shows

`POST /api/feedback` with JSON:

```ts
{ kind: 'bug' | 'feature', description: string,
  context?: { version, sha, track, device /* phone | tablet | desktop */, ua, screen, error /* last uncaught error */ },
  name?: string, secret?: string,    // the scoreboard name and device secret, only when this device has a name
  images?: [{ name, type: 'image/jpeg', data: /* base64 */ }] }   // up to 3 pictures, see below
```

The issue: title `[bug] <first line>` or `[feature] <first line>` (70 characters, `@` written `(at)`); body with the
scoreboard name (only when the device secret owns that name, `src/scoreboard/owner.ts`; otherwise `anonymous`), the
description, the context lines and the last error, each inside a `~~~text` code fence, so nothing the player typed
renders as markup, links or mentions. Labels: `from-game` and `bug` or `feature`. No email field; the form says in one
line that the report and the name are public. The secret is never written to the issue or stored.

Answers: `200 { ok, number, url }` (a repeat of the same report within 10 minutes answers the first issue with
`duplicate: true`), 400 bad JSON, 403 foreign origin, 405 not POST, 409 the same report is already being filed (or
GitHub did not answer it in time), 413 body over 4 KB, 415 not JSON, 422 empty / over-long description or a wrong kind,
429 rate limited (`Retry-After`), 502 GitHub refused, 503 no token configured, 504 GitHub did not answer in 10 s.

## Pictures (owner, 27 Oct 2026)

The report box takes up to **3 pictures**: paste (Ctrl/Cmd+V anywhere on the page), drag and drop onto the box, or the
"Add a picture" file input. The browser shrinks each (longest side 1600 px, JPEG quality 0.85; if still over 600 KB it
tries smaller steps; over 900 KB after that it is refused with a message) and refuses to send a body over 2.5 MB.
The request carries the header `X-Feedback-Images`; only then does the Function accept a body past 4 KB (up to 3.8 MB;
Vercel's own limit is 4.5 MB).

Server checks (any failure = `400` with the reason, nothing filed): at most 3; `type` image/jpeg or image/png; strict
base64; magic bytes match the type (FF D8 FF / 89 50 4E 47); each at most 900 KB decoded; together at most 2.5 MB.

Valid pictures are committed with the same token through the contents API to the branch **`feedback-images`**
(created from the default branch's HEAD the first time) at `feedback-images/<yyyy>/<mm>/<unix ms>-<n>.jpg`, commit
message `feedback image for a report`, uploaded in parallel inside a 6 s budget (a 409 race is retried once). The issue
embeds them under `## Pictures` as `![picture n](https://raw.githubusercontent.com/hartmanc/probe_sim/feedback-images/<path>)`.
These links render for logged-out viewers only while the repo is public. **Fallback:** if an upload fails (403 = the
token lacks Contents write, 422, network) the issue is still filed as text with
`_n picture(s) could not be uploaded (HTTP <status>)_`; the answer is `{ ok, number, url, images: { uploaded, failed } }`
and the toast says "pictures could not be uploaded". Uploads sit under the same rate limit (3 reports per IP per 10 min);
no new endpoint.

## Limits

| rule | value | where |
|---|---|---|
| same origin | a present `Origin` must be the request host or in `SCOREBOARD_ALLOWED_ORIGINS` | `src/scoreboard/http.ts` |
| rate limit | 3 reports per IP per 10 min (`sb:rl:feedback:<ip>`, the scoreboard's Redis) | `FEEDBACK.perIp` |
| body | 4 KB (3.8 MB with the `X-Feedback-Images` header, for pictures): Content-Length checked first, then the stream is cut off past 4096 bytes whatever it claimed | `readCapped` |
| description | 1-2000 characters after control and format characters are stripped | `parseFeedback` |
| duplicates | IP + kind + description hashed, `sb:fbdup:<sha256>` for 10 min: a retry or double tap never files twice | `FEEDBACK.dedupeS` |
| upstream | GitHub must answer in 10 s (AbortSignal); after a timeout the duplicate key stays, so a retry gets 409 | `FEEDBACK.upstreamTimeoutMs` |

## The token (owner)

1. GitHub → Settings → Developer settings → Fine-grained personal access tokens → Generate: repository access **only
   hartmanc/probe_sim**, permissions **Issues: Read and write** and, for the pictures, **Contents: Read and write** (nothing else), an expiry you will renew.
2. Vercel → the project → Settings → Environment Variables: `GITHUB_ISSUES_TOKEN` = the token, for Production (and
   Preview if you want reports from previews). Check presence with `vercel env ls`, never print it.
3. On the repo, create the labels `from-game` and `feature` (`bug` exists by default).
4. Until the token has Contents write, reports are filed as text only (the fallback above). To turn pictures on: edit
   the token's permissions on GitHub (Contents: Read and write on hartmanc/probe_sim) and re-save it in Vercel.
5. Without the variable the function answers 503 and the button says reports are not set up.

## Releasing a scoreboard name (owner)

The issue may name a scoreboard player; names belong to devices (`docs/scoreboard.md` §1.1). To release one in the
Upstash console: `DEL sb:own:<lower-cased name>` and `DEL sb:xfer:<lower-cased name>`. The next device to post the name
claims it; its board entries stay (remove one with `ZREM sb:z:<board> "<name>"` and `HDEL sb:h:<board> "<name>"`).
