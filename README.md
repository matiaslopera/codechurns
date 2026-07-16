# CodeChurns — AI Customer-Retention Agent

AI agent that detects customer churn risk for recurring-revenue SMEs (salons, gyms, spas) in Latin America, and recommends what to do about it. Built for the UC Berkeley AI Leadership Intensive.

## What it does

The owner uploads their appointment/sales history (CSV or Excel). The app automatically detects the relevant columns, calculates each customer's normal visit cycle, and flags who's drifting away from their usual rhythm — before it shows up as lost revenue. Each flagged customer gets a plain-language explanation grounded only in their real data, plus a suggested action (reminder, discount, personal call). The owner always approves, edits, or discards each action — the app never contacts a customer on its own.

## Built with

Python, Streamlit, pandas. Built end-to-end with Claude Code across 5 iterative phases (see commit history / git tags v1.0.0 → v1.5.1), each one tested before moving to the next.

## AI collaboration

This project was built in close collaboration with Claude Code, from architecture proposals to implementation and testing. Every phase followed the same loop: propose a plan → confirm scope → implement → run tests → verify in the browser before moving on. All AI-suggested design decisions (e.g. rule-based templates instead of an LLM for explanations, to guarantee zero hallucination) were reviewed and approved by the team before merging.

## How to run it

\⁠ \ ⁠\`bash
pip install -r requirements.txt
streamlit run app.py
\⁠ \ ⁠\`

Try it with the sample data in ⁠ sample_data/ ⁠.

## Project origin

This project's PRD was designed by another team in our program and handed to us through an in-class exchange. We built it end-to-end, and extended it in several ways beyond the original spec (see version history below).

## Version history

•⁠  ⁠*v1.0.0* — Core MVP: file ingestion with automatic column detection, risk engine (median visit cycle + configurable deviation threshold), rule-based explanations and suggested actions (no LLM — zero hallucination risk), approve/edit/discard review panel, Excel export with risk-tier colors, hardened against real-world edge cases (ambiguous columns, currency symbols, duplicate rows). Bilingual ES/EN from day one.
•⁠  ⁠*v1.1.0* — Review panel redesigned from cards to a table layout for faster scanning.
•⁠  ⁠*v1.2.0* — Owners can now reclassify the suggested strategy (reminder/discount/call) for any customer, and enter an exact custom discount amount.
•⁠  ⁠*v1.3.0* — Merged in a teammate's feature (ready-to-send customer message with adjustable tone) via a real git merge between independent branches. The custom discount amount from v1.2.0 now flows into the generated message.
•⁠  ⁠*v1.4.0* — Risk threshold is now adjustable from the sidebar (no code changes needed).
•⁠  ⁠*v1.5.0* — Added a one-click useful/not-useful feedback control per recommendation (per the original PRD's US5), logged for human review.
•⁠  ⁠*v1.5.1* — Visual polish for Demo Day: wide layout, legible dropdown columns, dark theme with accent color — no logic changes.

## Team

Built by Diego Bahena Trujillo, Fernanda Daniela Hernández Iturbe, María Camila Rojas Caden, Matías Lopera Arango, Rebecca Astrid Miyano Vázquez as part of the UC Berkeley AI Leadership Intensive, July 2026.

