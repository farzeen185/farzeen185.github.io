# Academic research presentation

Farzeen Khan, MS in Water Engineering and Management, Asian Institute of Technology.
Advisor: Dr. Natthachet Tangdamrongsub.

The deck uses the Metropolis Beamer theme with a navy and teal research palette and sans-serif typography. The editable PowerPoint follows the same visual hierarchy. The main talk contains slides 1–35; conclusions are on slide 34 and selected references on slide 35. Slides 36–50 are supporting results for questions, including all 22 basin rows for observed trends, TWS/GWS climate-model performance, GLDAS comparison and groundwater consistency. For a shorter seminar, the full basin tables can remain in backup.

Present the PDF in full-screen mode or use the editable PPTX. The scientific plots use vector PDFs in Beamer and high-resolution images in PowerPoint. Text and the 19 PowerPoint tables remain editable. Reservoir points represent actual scene-supported observations; long gaps are not connected.

## Compile the Beamer source

Unzip this archive and run twice from its folder:

    xelatex -interaction=nonstopmode -halt-on-error Thailand_Academic_Metropolis.tex
    xelatex -interaction=nonstopmode -halt-on-error Thailand_Academic_Metropolis.tex

Use an up-to-date TeX Live or MiKTeX installation containing Beamer, Metropolis, fontspec, booktabs and the standard graphics/math packages. The source uses Arial when available and falls back to TeX Gyre Heros. All referenced vector figure files are supplied in figures/. No workstation-specific image path is required for compilation.

## Sources and rebuilding

Theme: Matthias Vogelgesang and contributors, Metropolis, https://github.com/matze/mtheme . The installed theme is an external TeX dependency, not bundled or relicensed here.

Scientific results and inputs: https://github.com/pratikkhanal16/thailand-water-storage-dss . Run the full scientific workflow first. Set TWSA_RESEARCH_ROOT to its completed work directory and run document_source/50_academic_metropolis.py to regenerate scientific figures, shared slide content and Beamer source. Script 51 generates editable PowerPoint using the original Codex artifact-tool runtime; PDF compilation does not require that runtime. Statistical models and saved scientific results are unchanged by this presentation redesign.

## Speaker guide

Explain the three objectives first. Distinguish observed storage O, naturalized baseline C and the paired historical run A before presenting the residual R. The accounting identity R = H + E retains the model discrepancy explicitly. State what each evaluation target measures: the naturalized parent for climate reconstruction, matching land compartments for GLDAS, and observation consistency for wells and reservoirs. Groundwater head and storage have different units; the study does not invent aquifer storage coefficients. The main conclusion is national decline with greater uncertainty in local rankings and human attribution.
