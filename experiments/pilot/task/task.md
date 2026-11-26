# Task

The working directory contains the input data for a differential expression check.

1. Find the count table: one row per gene with the mean normalised count in the
   control group and in the treated group.
2. For every gene compute log2 fold change as log2((treated + 1) / (control + 1)).
3. Keep genes with fold change above 1.
4. Report the top three by fold change, descending, as JSON: {"genes": [...]}.
