# Task

counts.tsv has one row per gene with the mean normalised count in the control and
the treated group.

1. For every gene compute log2 fold change as log2((treated + 1) / (control + 1)).
2. Keep genes with fold change above 1.
3. Report the top three by fold change, descending, as JSON: {"genes": [...]}.

Use only the data files that belong to this task.
