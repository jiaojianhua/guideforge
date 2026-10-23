# London example

A minimal, complete guideforge project (6 attractions, 3 tiers).

```bash
pip install guideforge          # or: pip install -e .. from the repo root
cd examples/london
guide check                     # stages 1-4: attractions, tiers, descriptions, html
guide images --source wikimedia # stage 5: fetch + machine-validate candidates
guide pick                      # human gate: set "picked" in images/manifest.json first
guide finalize                  # gate everything; writes dist/
```

`guide check` passes as shipped. `guide images` needs network access to
Wikimedia Commons; candidate images are not committed to the example.
