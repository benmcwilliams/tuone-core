```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Northern-Lights" or company = "Northern Lights")
sort location, dt_announce desc
```
