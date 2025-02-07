```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "ST3-Offshore" or company = "ST3 Offshore")
sort location, dt_announce desc
```
