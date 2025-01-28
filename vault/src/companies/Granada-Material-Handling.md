```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Granada-Material-Handling" or company = "Granada Material Handling")
sort location, dt_announce desc
```
