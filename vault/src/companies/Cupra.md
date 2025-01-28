```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Cupra" or company = "Cupra")
sort location, dt_announce desc
```
