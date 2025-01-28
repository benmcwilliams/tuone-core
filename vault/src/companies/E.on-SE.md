```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "E.on-SE" or company = "E.on SE")
sort location, dt_announce desc
```
