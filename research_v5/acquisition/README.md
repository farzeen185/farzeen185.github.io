# Optional upstream acquisition

The complete scientific run uses the supplied compact, checksummed inputs and performs no network download. These two scripts additionally document acquisition of source-global CSR data and the public MSEA-Res archive. They are not required for a professor to reproduce the released analysis.

Set each script's ROOT to a chosen workspace before use, or place the script in that workspace's `scripts/` directory. The CSR script downloads three provider files and retains Thai subsets, source attributes, hashes and a special-month audit. The MSEA script downloads the original 116 MB reservoir archive and saves its Zenodo metadata. The analysis uses a separately retained monthly Thai subset, keeping Level-1 scene sampling distinct from provider-filled Level 2.

Provider URLs may serve revised files in the future. Acquisition dates and SHA-256 provenance identify the release inputs; newly downloaded files are not assumed identical to the frozen compact inputs. Consult the source licenses and citations before reuse.
