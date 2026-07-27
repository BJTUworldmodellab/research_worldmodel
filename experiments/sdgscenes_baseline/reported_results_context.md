# Reported-results Context Policy

## Purpose

This file defines how to mention SDGScenes official reported numbers if a paper result table is found.

## Rule

Reported SDGScenes numbers must not be mixed into the direct ranking table unless we reproduce them under the same protocol.

Use a separate table titled:

> Reported results from related systems under their original protocols

## Required columns

| Field | Required content |
|---|---|
| Method | SDGScenes official |
| Source | paper / supplementary / author page URL |
| Dataset | original dataset and split |
| Input protocol | original input type |
| Metrics | original metrics exactly as reported |
| Output representation | original representation |
| Directly comparable to ours? | no, unless protocol fully aligned |
| How used | context only; not ranked |

## Safe caption

> These numbers are copied from the original papers and are not directly comparable to our InstructScene-protocol results because the input protocols, datasets, and evaluators differ.

## Current state

No official SDGScenes reported-results table has been entered into this package yet. If found later, add source URL, table number, exact metric names, and a note explaining why it remains separate from our direct comparison.

