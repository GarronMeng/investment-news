# BidClub Expert Intelligence

## Goal

Use BidClub's keyless podcast API as a high-value expert-opinion layer for the investment research system. The layer is designed to surface non-consensus industry observations and thesis changes without allowing soft commentary to overwrite hard market evidence.

## Pipeline

`BidClub latest episodes -> TL;DR/digest -> watchlist/topic mapping -> expert_intelligence.json -> Daily Flash sidecar`

The first version uses title, dek, TL;DR and digest. Full transcripts remain available through the stored BidClub episode URL and source URL, but are not copied into the repository by default.

## Output contract

`expert_intelligence.json` contains:

- source status and coverage summary;
- ranked relevant episodes;
- matched topics and watchlist assets;
- transparent keyword/trigger hits;
- conservative candidate stance (`positive_candidate`, `negative_candidate`, `mixed_candidate`, `review_required`);
- per-asset `attention_boost` from 0-15;
- BidClub and original-source provenance links.

`daily_flash.json` receives the same information under `expert_intelligence`.

## Safety boundary

BidClub is an expert-opinion sidecar, not a hard-event feed. Version 1 therefore does **not** change the Decision Matrix directional composite score. Candidate stance is only an instruction to review the underlying thesis.

Before a view can affect directional conviction it should be cross-validated against at least one harder source such as company filings/earnings, pricing or shipment data, macro data, fund/market flows, or price/volume behavior.

## Suggested phase 2

After enough observations are accumulated, evaluate whether expert intelligence adds measurable signal quality. Only then consider a sixth Decision Matrix layer, with a lower weight than hard events and explicit source-quality/recency decay.
