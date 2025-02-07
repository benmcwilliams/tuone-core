```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Skovgaard-Energy" or company = "Skovgaard Energy")
sort location, dt_announce desc
```
