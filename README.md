# Velvet Unicorn Skills Library

Public repository of skills for Moltbot (formerly Clawdbot) — including the **Velvet Unicorn** skill for AI-powered token, wallet, and trading analysis via the VelvetDAO Unicorn `/ask` endpoint.

## Structure

Each top-level directory is a provider. Each subdirectory within a provider is an installable skill containing a `SKILL.md` and other skill-related files.

```
moltbot-skills/
└── velvet/
    └── velvet-unicorn/
        ├── SKILL.md
        └── scripts/
            ├── ask_unicorn.py
            └── ask_unicorn.sh
```

## Install Instructions

Give Moltbot the URL to this repo and it will let you choose which skill to install.

```
https://github.com/<YOUR_ORG>/<YOUR_REPO>
```

## Available Skills

| Provider | Skill          | Description                                                                                                                                                                 |
| -------: | -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|   velvet | velvet-unicorn | Calls VelvetDAO Unicorn AI (`POST /ask`) to answer token analysis, wallet analysis, and trade analysis questions. Returns `{ meta_category, vu_category, answer, txdata }`. |

## Skill Overview: velvet-unicorn

The `velvet-unicorn` skill is a thin wrapper around:

* **Endpoint:** `POST https://gentweet.velvetdao.xyz/ask`
* **Purpose:** Provide natural-language answers for:

  * Token information & analysis
  * Wallet analysis
  * Trading / “should I buy/sell” analysis (may return tx intent data)

### Request Format

The helper scripts send JSON shaped like:

```json
{
  "question": "string",
  "context": "string",
  "userid": "string | null",
  "userid_sol": "string | null",
  "previous_questions": ["string", "..."]
}
```

### Response Format

The endpoint is expected to return:

```json
{
  "meta_category": 0,
  "vu_category": 1,
  "answer": "string",
  "txdata": { "..." : "..." }
}
```

* `answer` is the text response you show the user.
* `txdata` may be `null` or `{}`; if present, treat as *proposed* transaction data (not executed).

## Usage

### Bash wrapper

```bash
bash velvet/velvet-unicorn/scripts/ask_unicorn.sh \
  "Analyze $TOKEN and summarize risk + momentum" \
  "User is interested in short-term swing trades; medium risk tolerance." \
  "0xYourEvmWallet" \
  "" \
  '["compare $TOKEN to $OTHER","what is the downside risk?"]'
```

### Python script

```bash
python3 velvet/velvet-unicorn/scripts/ask_unicorn.py \
  --question "Analyze $TOKEN and summarize risk + momentum" \
  --context "User is interested in short-term swing; medium risk tolerance." \
  --userid "0xYourEvmWallet" \
  --userid-sol "" \
  --previous-questions '["compare $TOKEN to $OTHER","what is the downside risk?"]'
```

### Environment Variables

* `VELVET_UNICORN_ENDPOINT` (optional) — override default endpoint (`https://gentweet.velvetdao.xyz/ask`)
* `VELVET_UNICORN_API_KEY` (optional) — if your endpoint requires auth, sent as `Authorization: Bearer <key>`

## Contributing

Community contributions are welcome. Here’s how to add your own skill:

### Adding a New Skill

1. Fork this repository and create a new branch for your skill.
2. Create a provider directory (if it doesn’t exist):

```bash
mkdir your-provider-name/
```

3. Add the required files:

   * `SKILL.md` — the main skill definition (required)
   * `references/` — supporting docs (optional)
   * `scripts/` — helper scripts (optional)

4. Follow the structure:

```
your-provider-name/
└── your-skill-name/
    ├── SKILL.md
    ├── references/
    │   └── your-docs.md
    └── scripts/
        └── your-script.sh
```

5. Submit a Pull Request with a clear description of your skill.

### Guidelines

* Keep skill definitions clear and well-documented
* Include usage examples in `SKILL.md`
* Test your skill before submitting
* Use descriptive commit messages
