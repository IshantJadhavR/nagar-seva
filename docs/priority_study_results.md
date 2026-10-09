# Priority engine v2 – decisions and results

## Final calls (made by Claude, as the project's "second and third team-mates")
1. **Hygiene / public-health problems are always High**: garbage, overflowing bins, dead animals, mosquitoes, stagnant or dirty water, blocked/overflowing drains, uncovered food, contaminated tap water. (The student's decision.) Only mild wording (silt with no overflow) stays Medium.
2. **Footpath / stall blocking**: Low if the duration is short or unstated, Medium if >= 7 days or "for months / long time". Never High on its own. A broken footpath is Low.
3. **Road surface damage (pothole, broken road) is High by default** because of accident risk. Near-miss or injury reported -> Critical.
4. **Critical is reserved for emergencies** (live/exposed wire, open manhole, sewage in drinking water, major flooding, electric shock, injury/near-miss). Points alone never give Critical, so the urgent queue is not flooded.
5. **Broken streetlight and no/low water supply = Medium**; contaminated water = High.
6. **Other**: a service failure (buses, noise, signals) = Medium; a pure information request = Low.

## Result (100 complaints; reference = student's round-1 ratings, with rubric-v2 re-rating of 51 hygiene/footpath items by Claude)
| | exact | within 1 level | weighted kappa | High+ recall |
|---|---|---|---|---|
| v1 engine, all 100 | 25% | 65% | 0.23 | 10% |
| v2, tuned on set A (48) | 98% | 100% | 0.99 | 96% |
| **v2, held-out set B (52)** | **87%** | **98%** | **0.87** | **90%** |

Set B is the honest number. Known misses: traffic signal showing conflicting signals (should be Critical), "exposed wiring" streetlight, multiple dead streetlights, flickering light near hospital.

## Limitations (say these in the viva)
- Word lists were written after seeing all 100 complaints, so B is not perfectly clean; real accuracy is likely lower.
- The reference is partly derived from the rules themselves (circular), the raters are 1 human + 1 AI, and the data is synthetic.
- Weights are a documented policy, not learned. Next step: have 2-3 real raters (or an officer) label ~100 new complaints.
