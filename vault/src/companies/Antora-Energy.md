```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Antora-Energy" or company = "Antora Energy")
sort location, dt_announce desc
```
