# Section 139(9) workflow

Tax Mitra treats a Section 139(9) notice as a partial-support workflow. It
does not decide whether a legal position is correct, create an ITR JSON file,
or submit to the Income Tax Department.

## Grounding

The workflow is grounded in the Income Tax Department's current e-Proceedings
manual and FAQ:

- [How to respond to Defective Return Notice u/s 139(9)](https://www.incometax.gov.in/iec/foportal/help/all-topics/e-filing-services/prima%20facie%20adjustment-UM)
- [e-Proceedings User Manual](https://www.incometax.gov.in/iec/foportal/help/respond-to-e-proceedings)

The official flow says the taxpayer can choose Agree or Disagree. Agree leads
to the applicable correction/response mode and ITR/JSON steps; Disagree
requires written reasons. The official guidance says the response window is
15 days from receipt unless the notice specifies another duration, and that a
submitted response cannot be edited or withdrawn.

## Tax Mitra flow

1. Confirm the extracted defect wording against the notice.
2. Ask whether the taxpayer agrees or disagrees; Not sure stops safely.
3. For Agree, record the taxpayer's intended online or offline/JSON route and
   prepare a correction action plan.
4. For Disagree, collect the taxpayer's own reason and prepare reviewable
   remarks without adding a legal conclusion.
5. Show the notice, filed-return details and applicable correction records as
   an evidence checklist.
6. Require human review before the official e-Filing portal handoff.

## Supported scenarios

- One or more extracted defects with clear original wording.
- TDS/receipt reporting defects, PAN/name mismatch wording, business statement
  defects, and other notice-specific defect text.
- Agree with a taxpayer-selected correction route.
- Disagree with taxpayer-supplied remarks.

## Safe boundaries

- No extracted defect wording: safe stop.
- Extraction not confirmed: safe stop.
- Taxpayer is Not sure about Agree/Disagree or the correction route: safe stop.
- Tax Mitra does not determine the applicable ITR type, generate/validate
  JSON, decide revised/fresh-return eligibility, or submit the response.
- The notice's stated deadline takes precedence. Tax Mitra does not infer a
  due date from issue date alone because the official default is measured from
  receipt.
