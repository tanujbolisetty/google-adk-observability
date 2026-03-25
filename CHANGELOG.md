# 📦 Changelog & Release Notes

## [1.2.1] - 2026-03-25
### ✨ New Features
- **Total User Questions Metric**: Added a new top-level `stat` panel to the Home Dashboard counting all human prompts, positioned directly beside "Total Sessions" for immediate volume visibility. Sourced from `v_aaa_user_intent`.

## [1.2.0] - Dashboard Evolution & Forensic Precision

### ✨ New Features
- **Symmetric Navigational Architecture**: Redesigned the suite's variable propagation logic. Summary dashboards (Home, FinOps, Diagnostics, Guide) now load in an "Overview" default state (`All`), while strictly passing explicitly selected User/Session tokens to Forensic dashboards (Traces, Transcripts, LLM Audit). This eliminates historical "Blank Box" filter regressions.
- **Visual Navigation Grouping**: The universal dashboard navigation header (`id: 999`) has been upgraded from a flat link list into three distinct, pill-styled contextual blocks (**📊 SUMMARY**, **🔍 FORENSICS**, **📚 RESOURCES**), dramatically improving visual hierarchy and operator focus.
- **Transcript Interaction Duration**: The Chat Transcripts dashboard now features a new `duration` column. By utilizing BigQuery's `LAG()` window function on chronological timestamps, the dashboard dynamically calculates and cleanly formats (e.g., "8 s") the exact interval between human and agent message turns.

### 💄 UI & UX Improvements
- **Dashboard Gallery**: Embedded 10 comprehensive screenshots into the `README.md` to showcase the Agent Home, FinOps, Diagnostics, Transcripts, Traces, and LLM Audit interfaces visually.
- **Guide Dashboard Overhaul**: The instructional documentation within the Guide dashboard has been spaced out via physical transparent spacer panels for distinct visual tracking. Panel heights were optimized to safely eliminate internal scrolling, and markdown headings were promoted for improved readability at a glance without sacrificing screen real estate.
- **SEO & Searchability**: Updated `README.md` introducing natural keywords ensuring correct repository indexing for developers searching for terms like "BigQuery Agent Analytics Plugin", "LLM Observability", and "Grafana Dashboards".

### 🐛 Bug Fixes & Under-The-Hood Stability
- Re-enabled `includeAll: true` on `user_id` and `session_id` strictly within the Guide dashboard variables logic, ensuring it acts as a smooth pass-through layer for sync without disrupting global context.
- Hardened variable handling in Home dashboard "Exit Actions" to strictly enforce overview-to-forensic flow without backward filter bleed.

---

*This release reinforces the Google ADK observability suite as a production-grade monitoring tool, explicitly solving complex navigation state loss and vastly improving the ease of diagnostic reading.*
