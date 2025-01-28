```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Geomachine" or company = "Geomachine")
sort location, dt_announce desc
```
