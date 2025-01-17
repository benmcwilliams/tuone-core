```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "German Aerospace Center (DLR)"
sort location, dt_announce desc
```
