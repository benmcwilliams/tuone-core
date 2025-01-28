```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "ArcelorMittal-Energy-S.C.A." or company = "ArcelorMittal Energy S.C.A.")
sort location, dt_announce desc
```
