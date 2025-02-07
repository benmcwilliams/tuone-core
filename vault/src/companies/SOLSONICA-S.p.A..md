```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "SOLSONICA-S.p.A." or company = "SOLSONICA S.p.A.")
sort location, dt_announce desc
```
