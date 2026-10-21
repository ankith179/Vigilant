# Recorded API-change demonstration

This is an executed model-enabled investigation, not a mock screen or an invented scenario result.

Recorded run: `experiments/pipeline/20261006T195007-e56e6b8d/results.json`.
Baseline: `1762adac607a1b29cfc4da129557780beea71616`.
Changed commit: `892a3d5213e950be40467f4a0c8cfb33d12e8132`.

The controlled mutation changes the backend route prefix from `/items` to `/catalog` in `backend/app/api/routes/items.py`. The generated frontend client remains unchanged. The commit is reproducible from its saved ChangeBench contract.

The workflow executed 12 recorded tool stages, detected 11 changed artifact records, proposed 33 affected-artifact candidates, and verified 24 evidence excerpts against repository snapshots.

There are ten lost graph-endpoint findings and five potential obsolete-client findings. Several refer to the same route-renaming cause; these are not fifteen independently confirmed defects.

## Example finding

Status: **POTENTIAL_INCONSISTENCY**.
Reason: A previously matched literal API disappeared while its consumer retains the old contract. Dynamic routes remain unresolved.

Evidence `41a15f4d521cebdbac2a7cbb8cad870a53288742fccc9cdb0b1183a335c3bf7a`: `frontend/src/client/sdk.gen.ts`, lines 340–343, commit `892a3d5213e950be40467f4a0c8cfb33d12e8132`.

```
        return (options.client ?? client).get<itemsReadItemResponses, itemsReadItemErrors, ThrowOnError>({
            responseType: 'json',
            security: [{ scheme: 'bearer', type: 'http' }],
            url: '/api/v1/items/{id}',
```

Evidence `9eea84b8166dd76aa7defb533e52b66408b3c34bee5cbabfcdee474e76668a6e`: `backend/app/api/routes/items.py`, lines 48–58, commit `1762adac607a1b29cfc4da129557780beea71616`.

```
@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get item by ID.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return item
```

## Model and verification

The local Qwen model returned **UNCERTAIN** with valid JSON and supplied evidence identifiers. The model decision is separate from the rule findings. Exact quote validation passed; semantic entailment has not been independently reviewed.

Recorded runtime: 33.65 seconds. All 12 tool stages completed successfully. These observations establish that the pipeline executes; they do not establish independent impact precision or superior consistency classification.

## Reopen the demonstration

Start the local application, choose the `vigilant` project and the imported controlled API-change repository, and open the analysis report, evidence, agent investigation and knowledge graph pages. Match the commit above. The saved report is also directly inspectable as JSON if a browser is unavailable.
