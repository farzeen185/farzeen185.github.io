# Rebuilding document and presentation sources

Numerical reproduction is automated by `../run.py` and requires no office software. The document sources are supplied separately because Word pagination and the editable PowerPoint builder have different runtime requirements.

After completing the scientific run, set `TWSA_RESEARCH_ROOT` to the absolute work directory. Install `python-docx` in the document Python environment. Run `23_write_extended_study.py` and `24_manuscript_v5.py`; the retained AIT template and citation metadata in this directory are fallback inputs. The author fonts are Times New Roman, body 12 pt and AIT chapter headings. On Windows with Microsoft Word, `render_v5_with_word.ps1 -InputDocx ABSOLUTE_DOCX -OutputPdf ABSOLUTE_PDF` updates fields and exports PDFs. Pagination may differ across fonts and Word versions; the released PDF is the reviewed 60-page version.

For the revised documents requested with spatial and temporal figures, run **`38_revise_spatiotemporal_documents.py`** after the full scientific run (including script 37). It incorporates 21 thesis figures and 22 manuscript figures and retains the 60-page thesis structure. Scripts 23 and 24 are the retained base writing modules, not the final figure revision by themselves. Run `40_revise_figure_presentations.py` after script 25 to produce the revised 42-slide source. The current released source ZIP already contains all required vector figures.

`25_slides_latex_v5.py` regenerates the shared slide JSON and self-contained Beamer source using the scientific environment. Compile twice from the presentation output directory with `xelatex -interaction=nonstopmode -halt-on-error Thailand_Attribution_Credibility_Beamer.tex`. Times New Roman must be installed, or replace its two fontspec declarations with a locally available serif font. The released source ZIP already contains the required vector figures.

`build_powerpoint_artifact_tool.mjs` records the editable PowerPoint authoring source. It uses OpenAI's artifact-tool runtime and the original local presentation path; change ROOT for another workspace with that runtime. Public scientific reproduction and Beamer compilation do not depend on this authoring library. The released PPTX remains editable in PowerPoint.

The latest report uses simpler prose and a step-by-step methodology. After the complete scientific run, run 43_simplify_report.py to rebuild this report directly; it reuses the figure layout from script 38 without rewriting the manuscript. Export the DOCX with the Word script above. This changes the report explanation only; it retains 60 pages, 21 figures and six tables. The previous manuscript and presentations remain the reviewed figure-rich versions.


For the final report with basin tables and forcing figures, run 46_append_basin_forcing_report.py after the full numerical run (which now includes script 45). It rebuilds the 60-page main report with script 43, then adds 23 appendix pages. The released final report has 83 pages, 31 figures and 17 tables. Script 43 alone remains the simpler main report source.
