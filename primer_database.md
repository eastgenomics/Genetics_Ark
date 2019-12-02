# 28/11/19

### Goal: Finish primer database bc Jethro has loads of stuffs

Agreed upon modifications:
- Add "blue" button (SNP check) --> done
- Add button for last date used (editing mode)
- Editing primers make the SNP status value to go null --> modify behaviour --> done
- Popup message for recalculating coverage
- Fix refreshing page after filtering (it keep the previous filtering constraints) --> done
- Ordering of main table
- Fluff stuff (padding, make it pretty) --> padding fixed (for this branch only)
- Excel importing mess
- Filter using position: handle single primers (it uses coverage for now)

# 29/11/19

Jethro wants tagging of which primer in a pair maps (strand dna) 

# 02/12/19

Occasions where 4 primers were linked by the same pair ID --> fixed in the primer import
if primers has mutliple mappings (coverages in the excel), need to add a check or something in import