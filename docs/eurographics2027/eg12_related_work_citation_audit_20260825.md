# EG12 related-work and citation audit

Date: 2026-08-25  
State: `EG12_CITATIONS_VERIFIED`

## Outcome first

The manuscript's indoor-synthesis, language/graph-conditioned generation, strong relation-aware systems, and relation-benchmark discussion has been reconciled against primary publication records. RelScene is now included as evaluation context. ReSpace remains cited as a 2025 arXiv preprint, not as an accepted ICLR paper. SDGScenes is described as a more complete user-intent/constraint system and is not placed in the direct numerical ranking.

## Verified bibliography inventory

| Key | Work | Publication record used | Verified fields |
|---|---|---|---|
| `lin2024instructscene` | InstructScene | [ICLR 2024/OpenReview](https://openreview.net/forum?id=6d9694oe9d) | authors, title, venue, year |
| `paschalidou2021atiss` | ATISS | [NeurIPS 2021 proceedings](https://proceedings.neurips.cc/paper/2021/hash/64986d86a17424eeac96b08a6d519059-Abstract.html) | authors, volume 34, pages 12013–12026 |
| `wang2021sceneformer` | SceneFormer | [IEEE DOI](https://doi.org/10.1109/3DV53792.2021.00021) | 3DV 2021, pages 106–115, DOI |
| `tang2024diffuscene` | DiffuScene | [IEEE DOI](https://doi.org/10.1109/CVPR52733.2024.01938) | CVPR 2024, pages 20507–20518, DOI |
| `fu20213dfront` | 3D-FRONT | [CVF open access](https://openaccess.thecvf.com/content/ICCV2021/html/Fu_3D-FRONT_3D_Furnished_Rooms_With_LayOuts_and_SemaNTics_ICCV_2021_paper.html) | ICCV 2021, pages 10933–10942 |
| `fu20203dfuture` | 3D-FUTURE | [arXiv record](https://arxiv.org/abs/2009.09633) | authors, title, preprint identifier |
| `zhai2023commonscenes` | CommonScenes | [DOI](https://doi.org/10.52202/075280-1307) | NeurIPS 2023, DOI |
| `feng2023layoutgpt` | LayoutGPT | [DOI](https://doi.org/10.52202/075280-0802) | NeurIPS 2023, DOI |
| `yang2024holodeck` | Holodeck | [CVF open access](https://openaccess.thecvf.com/content/CVPR2024/html/Yang_Holodeck_Language_Guided_Generation_of_3D_Embodied_AI_Environments_CVPR_2024_paper.html) | authors, CVPR 2024, pages 16227–16237 |
| `ye2024relscene` | RelScene | [ACM DOI](https://doi.org/10.1145/3664647.3681653) | authors, ACM MM 2024, pages 10563–10571, DOI |
| `bucher2026respace` | ReSpace | [arXiv record](https://arxiv.org/abs/2506.02459) | authors, current v6 title, 2025 preprint status, arXiv DOI |
| `gao2026sdgscenes` | SDGScenes | [Pattern Recognition DOI](https://doi.org/10.1016/j.patcog.2026.113674) | authors, volume 179, article 113674, 2026 |

## Protocol and claim classification

| Method/reference | Role in this paper | Same-protocol numerical rank? | Allowed wording |
|---|---|---:|---|
| InstructScene | fixed pretrained generator and direct baseline | Yes | compare under identical frozen validation prompts/checkpoints |
| Movement-matched random controls | causal-adjacent movement control | Yes | structured direction performs better than matched random movement |
| Generic relation optimizer | budget-matched defensive control | Yes | similar point estimate; superiority unresolved |
| ReSpace | strong text-driven synthesis/editing reference | No | different protocol; numerical claim requires shared-protocol reproduction |
| SDGScenes | stronger user-intent/constraint-system context | No | acknowledge broader semantic dependency/VLM/optimization scope |
| RelScene | spatial-relation benchmark context | No | motivates relation-aware evaluation; metrics and dataset differ |

## Manuscript claim audit

The revised Related Work text preserves these boundaries:

- no “state of the art” claim on text-driven 3D scene generation;
- no claim of outperforming ReSpace or SDGScenes;
- no “first relation-aware” claim;
- no universal visual-quality claim;
- no claim of complete commonsense, affordance, reachability, or support reasoning;
- reported external numbers are not mixed into the paper's direct-comparison table.

## Remaining citation risks

- Final PDF compilation must confirm that every citation resolves and that the EG bibliography style renders DOI/URL fields correctly.
- Publication metadata should be rechecked once more immediately before submission in case an online-first record changes issue/month formatting; this must not change scientific claims.
