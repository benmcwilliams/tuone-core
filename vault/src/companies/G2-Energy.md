```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "G2-Energy" or company = "G2 Energy")
sort location, dt_announce desc
```
