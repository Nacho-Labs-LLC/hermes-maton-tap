# Google Docs routing reference

## Grounding level

This reference is narrower than the Gmail and Google Calendar entries already proven in this repo.

What is grounded:
- `google-docs` already appears in this repo's `maton-connections` skill as a Maton app name.
- Maton's public `api-gateway-skill` repository documents the Google Docs route family below.
- The dedicated `maton-google-docs` helper in this tap now builds and tests requests against these shapes.

What is **not** claimed here:
- live authenticated success from this repo's validation environment
- exhaustive Google Docs feature coverage
- proof that every documented Google Docs mutation shape has been exercised through this tap

## Route family

App prefix:

```text
google-docs
```

Documented route pattern:

```text
/google-docs/v1/documents/...
```

## Core endpoints wrapped in this tap

### Get document

```bash
python scripts/maton_api_gateway.py get \
  --app google-docs \
  --path /v1/documents/<document-id>
```

Dedicated helper equivalent:

```bash
python ../maton-google-docs/scripts/maton_google_docs.py get <document-id>
```

### Create document

```bash
python scripts/maton_api_gateway.py post \
  --app google-docs \
  --path /v1/documents \
  --body '{"title":"Draft brief"}'
```

### Batch update document

```bash
python scripts/maton_api_gateway.py post \
  --app google-docs \
  --path /v1/documents/<document-id>:batchUpdate \
  --body @requests.json
```

Dedicated helper equivalents:

```bash
python ../maton-google-docs/scripts/maton_google_docs.py batch-update <document-id> --payload @requests.json
python ../maton-google-docs/scripts/maton_google_docs.py insert-text <document-id> --text 'Hello' --append
python ../maton-google-docs/scripts/maton_google_docs.py replace-text <document-id> --match '{{name}}' --replace 'Ada'
```

## Safety notes

- Start with `get` before mutation flows.
- Use `maton-connections` to confirm the target `google-docs` connection ID first.
- Treat write operations as route-shape wrappers unless and until you have real success against the intended account.
- For unsupported request types, use the generic gateway helper with an explicit JSON body instead of hand-waving about hidden support.
