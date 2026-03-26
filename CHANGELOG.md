## [1.2.3] - 2026-03-26
### 🛠️ Maintenance
- **Repository Optimization**: Removed `docker/` directory from Git tracking. Docker configuration is now treated as a local development utility to prevent project-specific configuration leakage.
- **Docker & K8s Alignment**: Updated `docker/entrypoint.sh` and `docker/k8s-deployment.yaml` to use standard template placeholders (`your-project-id`, `your-dataset-id`, etc.) for generic provisioning.
- **Git Hygiene**: Updated `.gitignore` to ensure Docker artifacts and local overrides are not tracked.

## [1.2.2] - 2026-03-25
### ✨ Branding & Layout
- **Branding Update**: Formally renamed the Home Dashboard landing to **"Google ADK Agent Analytics"**.
- **Layout Precision**:
    - Increased the "Welcome" panel height to remove the scrollbar.
    - Added a **"Questions Per Day"** trend beside "Sessions Per Day" (Width 12 each).
    - Expanded **"Daily Token Consumption"** to full-width (Width 24) for improved legibility of multi-line metrics.
    - Orchestrated a global grid shift to accommodate the expanded visualization row.

## [1.2.1] - 2026-03-25
### ✨ New Features
- **Total User Questions Metric**: Added a new top-level `stat` panel to the Home Dashboard counting all human prompts, positioned directly beside "Total Sessions" for immediate volume visibility. Sourced from `v_aaa_user_intent`. Includes clarification that count spans all sessions in the selected timeframe.
- **Updated Screenshots**: Injected the latest `Home_v2.jpg` assets to reflect the expanded 4-metric Home Dashboard layout in `README.md`.

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
