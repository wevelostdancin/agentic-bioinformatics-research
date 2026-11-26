# Task

The working directory contains a variant call table for one sample.

1. Find the variant table: one row per variant with chromosome, position,
   reference allele, alternate allele, quality, depth and filter status.
2. Keep only variants with filter status PASS, quality at least 30 and depth at
   least 10.
3. Rank the survivors by quality, descending; break ties by position, ascending.
4. Report the top three as strings of the form chrom:pos:ref>alt in a JSON
   object: {"genes": ["chr1:1234:A>G", ...]}.

The key is always called "genes" for compatibility with the harness.
