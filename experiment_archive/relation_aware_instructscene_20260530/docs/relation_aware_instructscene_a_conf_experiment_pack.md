# Relation-Aware InstructScene A-Conference Experiment Pack

Generated from synchronized full-run JSON files under `results/full`.

## Main Results

| Room | Scenes | Relations | Baseline | Ours | Gain | Overlap Base | Overlap Ours | OOB Ours |
|---|---|---|---|---|---|---|---|---|
| bedroom | 162 | 245 | 0.7388 | 0.8735 | 0.1347 | 0.0870 | 0.0836 | 0.0000 |
| livingroom | 192 | 294 | 0.5510 | 0.7415 | 0.1905 | 0.1399 | 0.1348 | 0.0000 |
| diningroom | 177 | 269 | 0.5948 | 0.7844 | 0.1896 | 0.1554 | 0.1542 | 0.0000 |

## Oracle Upper Bound

| Room | Baseline | Parsed | Oracle | Oracle Gap | Gain Captured |
|---|---|---|---|---|---|
| bedroom | 0.7388 | 0.8735 | 0.8857 | 0.0122 | 0.9167 |
| livingroom | 0.5510 | 0.7415 | 0.7755 | 0.0340 | 0.8485 |
| diningroom | 0.5948 | 0.7844 | 0.8141 | 0.0297 | 0.8644 |

## Repair Pass Ablation

| Room | Passes | Ours | Gain | Overlap Ours | OOB Ours | Edits |
|---|---|---|---|---|---|---|
| bedroom | p0 | 0.7388 | 0.0000 | 0.0870 | 0.0000 | 0 |
| bedroom | p1 | 0.8531 | 0.1143 | 0.0779 | 0.0012 | 45 |
| bedroom | p2 | 0.8735 | 0.1347 | 0.0836 | 0.0000 | 59 |
| bedroom | p3 | 0.8816 | 0.1429 | 0.0801 | 0.0012 | 68 |
| livingroom | p0 | 0.5510 | 0.0000 | 0.1399 | 0.0000 | 0 |
| livingroom | p1 | 0.7211 | 0.1701 | 0.1353 | 0.0000 | 62 |
| livingroom | p2 | 0.7415 | 0.1905 | 0.1348 | 0.0000 | 73 |
| livingroom | p3 | 0.7449 | 0.1939 | 0.1352 | 0.0000 | 78 |
| diningroom | p0 | 0.5948 | 0.0000 | 0.1554 | 0.0000 | 0 |
| diningroom | p1 | 0.7732 | 0.1784 | 0.1533 | 0.0000 | 57 |
| diningroom | p2 | 0.7844 | 0.1896 | 0.1542 | 0.0000 | 64 |
| diningroom | p3 | 0.7844 | 0.1896 | 0.1533 | 0.0000 | 68 |

## Distance Threshold Ablation

| Room | Setting | Ours | Gain | Overlap Ours | OOB Ours | Avg Move |
|---|---|---|---|---|---|---|
| bedroom | close0.50_far1.30 | 0.8735 | 0.1347 | 0.0857 | 0.0000 | 2.4199 |
| bedroom | close0.50_far1.60 | 0.8735 | 0.1347 | 0.0837 | 0.0000 | 2.5654 |
| bedroom | close0.75_far1.30 | 0.8735 | 0.1347 | 0.0856 | 0.0000 | 2.4223 |
| bedroom | close0.75_far1.6 | 0.8735 | 0.1347 | 0.0836 | 0.0000 | 2.5677 |
| bedroom | close0.75_far2.00 | 0.8694 | 0.1306 | 0.0837 | 0.0000 | 2.7940 |
| bedroom | close1.00_far1.60 | 0.8612 | 0.1224 | 0.0836 | 0.0000 | 2.4470 |
| bedroom | close1.00_far2.00 | 0.8571 | 0.1184 | 0.0837 | 0.0000 | 2.6624 |
| livingroom | close0.50_far1.30 | 0.7449 | 0.1939 | 0.1366 | 0.0000 | 2.3972 |
| livingroom | close0.50_far1.60 | 0.7415 | 0.1905 | 0.1354 | 0.0000 | 2.5020 |
| livingroom | close0.75_far1.30 | 0.7449 | 0.1939 | 0.1360 | 0.0000 | 2.4023 |
| livingroom | close0.75_far1.6 | 0.7415 | 0.1905 | 0.1348 | 0.0000 | 2.5059 |
| livingroom | close0.75_far2.00 | 0.7449 | 0.1939 | 0.1336 | 0.0000 | 2.7261 |
| livingroom | close1.00_far1.60 | 0.7075 | 0.1565 | 0.1350 | 0.0000 | 2.2835 |
| livingroom | close1.00_far2.00 | 0.7109 | 0.1599 | 0.1337 | 0.0000 | 2.4546 |
| diningroom | close0.50_far1.30 | 0.7844 | 0.1896 | 0.1550 | 0.0000 | 2.0425 |
| diningroom | close0.50_far1.60 | 0.7844 | 0.1896 | 0.1551 | 0.0000 | 2.1277 |
| diningroom | close0.75_far1.30 | 0.7807 | 0.1859 | 0.1541 | 0.0000 | 2.0491 |
| diningroom | close0.75_far1.6 | 0.7844 | 0.1896 | 0.1542 | 0.0000 | 2.1341 |
| diningroom | close0.75_far2.00 | 0.7844 | 0.1896 | 0.1529 | 0.0000 | 2.2789 |
| diningroom | close1.00_far1.60 | 0.7286 | 0.1338 | 0.1539 | 0.0000 | 1.8540 |
| diningroom | close1.00_far2.00 | 0.7286 | 0.1338 | 0.1525 | 0.0000 | 1.9720 |

## Multi-Seed Summary

| Room | N | Baseline mean | Baseline std | Ours mean | Ours std | Gain mean | Gain std | Overlap mean | Overlap std | OOB mean |
|---|---|---|---|---|---|---|---|---|---|---|
| bedroom | 3 | 0.7565 | 0.0209 | 0.8939 | 0.0178 | 0.1374 | 0.0125 | 0.0921 | 0.0075 | 0.0012 |
| livingroom | 3 | 0.5420 | 0.0086 | 0.7483 | 0.0180 | 0.2063 | 0.0246 | 0.1330 | 0.0037 | 0.0001 |
| diningroom | 3 | 0.5923 | 0.0021 | 0.7993 | 0.0170 | 0.2069 | 0.0187 | 0.1507 | 0.0068 | 0.0000 |

## Notes

- The overlap metric is a coarse 2D AABB footprint proxy, not full mesh collision.
- The default setting is `repair_passes=2`, `close_distance=0.75`, `far_distance=1.6`.
- Seed 2 bedroom has a small repaired center out-of-bounds rate, so final paper should either clamp stricter or report this honestly.
