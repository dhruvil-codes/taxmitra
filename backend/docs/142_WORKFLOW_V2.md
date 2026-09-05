# Tax Mitra 142(1) workflow v2

The 142(1) workflow keeps extraction and human confirmation as a hard boundary.
Once confirmed, the notice requests are exposed through
`GET /api/scrutiny/{notice_id}/requests`. Each request preserves
`original_text` and includes `technical_term`, `plain_meaning`,
`why_requested`, `possible_evidence`, `required_user_information`, `status`,
`confidence`, and `source_ids`.

Use `GET /api/scrutiny/{notice_id}/question-plan` for the minimum deterministic
question plan. It returns `question_id`, `question`, `why_we_are_asking`,
`type`, `options`, `related_request_ids`, `required`, `conditions`, and
`status`. Known document requests remain evidence recommendations and do not
become availability questions.

Use `POST /api/scrutiny/question-plan` with `notice_id` and an `answers` map to
receive conditional follow-up questions. The backend owns the decision logic.
The legacy `/api/scrutiny/{notice_id}/questions` endpoint remains unchanged for
existing clients. Both paths retain verified-source checks and safe refusal.

The 143(1)(a) workflow uses separate `/api/workflow/*` routes and is unchanged.
