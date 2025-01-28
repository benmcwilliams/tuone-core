```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Dragados-Offshore-S.A." or company = "Dragados Offshore S.A.")
sort location, dt_announce desc
```
