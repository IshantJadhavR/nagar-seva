# Priority rubric (v1)

Purpose: one shared definition of Low / Medium / High / Critical, so different raters (and the rule engine)
can be compared fairly. Rate from the complaint text alone. Do NOT look at the system's answer.

## The four levels

| Level | Meaning | Typical signs in the text |
|---|---|---|
| **Critical** | Danger to life **right now or very likely**. Needs action the same day. | Exposed or hanging live electric wire; open or uncovered manhole on a road or near a school; sewage mixing into drinking water; major flooding entering homes or shops |
| **High** | Real risk of injury or illness, **or** many people affected, **or** an essential service lost for days, **or** a hazard in a sensitive place (school, hospital) | Deep pothole where vehicles slip or fall; dog attacks on people; disease outbreak (dengue, fever); no water for a whole lane for days; broken road next to a school where children walk |
| **Medium** | Ongoing daily inconvenience or hygiene problem. Nobody is in immediate danger. | Garbage uncollected for days; blocked drain with smell; broken footpath; streetlight off; low water pressure; mosquitoes (without illness) |
| **Low** | Minor, cosmetic or one-off. Or not a municipal issue. | Noise, bus service, certificates, general feedback, a single flickering bulb, a stall slightly on the footpath |

## Questions to ask, in this order

1. Could someone be **killed or seriously hurt today** if nothing is done? -> **Critical**
2. Is there a stated **risk to people's safety or health**, or a **vulnerable place** (school, hospital, children, elderly), or **many people / a whole area** affected, or a **basic service (water) completely lost**? -> **High**
3. Is it a real municipal problem that makes daily life worse, but nobody is in danger? -> **Medium**
4. Otherwise -> **Low**

## Rules

- **Rate the problem, not the tone.** Anger, capital letters, "urgent" or "please" must not change the rating.
  A calm complaint about an open manhole is Critical; an angry complaint about a late bus is still Low.
- **A hazard needs to be stated or obvious.** "Pothole" alone is Medium. "Pothole where bikes are slipping"
  or "deep pothole near school" is High. Do not invent danger that the text does not suggest.
- **Duration matters only a little.** A problem lasting more than a week can move Medium up to High only if it
  affects health, safety or an essential service.
- **Location matters.** A school or hospital next to a hazard raises it. A school only mentioned as a landmark
  with a minor issue (for example a stall on the footpath) does not make it High.
- **Off-topic or unclear complaints are Low.**
- **When torn between two levels,** pick the higher one only if the text describes a danger to people.
  Otherwise pick the lower one.

## How the ratings are used

1. Each rater fills one sheet independently (no discussion).
2. Agreement between raters is measured with **Cohen's kappa** (weighted, because the levels are ordered).
   Rough guide: below 0.4 = rubric unclear, 0.4-0.6 = moderate, 0.6-0.8 = good, above 0.8 = very good.
3. The rule-based engine is compared with the raters. Disagreements are reviewed one by one; the engine's
   weights and word lists are adjusted only for reasons that make sense under this rubric, not just to raise
   the score.

## Honest limitations (copy into the report)

- Raters for this study: 1 human (the student) + 1 AI assistant, **not** several independent humans.
  The AI rater may share biases with the rule-engine's author (also an AI), so human agreement is the
  stronger evidence. Add more human raters if available.
- Text-only rating: map pin, photo and nearby places are not shown, but the engine normally uses them.
- 100 complaints, synthetic text. Results show consistency with this rubric, not real-world truth.
