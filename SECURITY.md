# Security scope

RE:MEMORY is a local, synthetic-data prototype. The public delivery page serves saved demonstration records, video and source downloads; it has no paid inference endpoint or personal-data upload form.

The FastAPI prototype uses one local demo identity and is not a production authentication system. Keep its binding at `127.0.0.1`; do not expose it with a public proxy or change it to `0.0.0.0` without adding authentication, access control, rate limits and an independent deployment review.

MixRoute credentials belong only in the local ignored `.env`. Source archives exclude `.env`, runtime databases, backups and private attachments. New records intended for publication must contain synthetic data and pass credential and privacy checks.

Model-generated artifacts remain CLAIM. Source/constraint checks, cost reservations and task idempotency are safeguards within the documented prototype scope, not a claim of complete semantic validation or penetration-test certification.

Do not post credentials or private user data in public issues.
