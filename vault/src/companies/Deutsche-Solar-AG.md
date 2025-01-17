```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Deutsche Solar AG"
sort location, dt_announce desc
```
