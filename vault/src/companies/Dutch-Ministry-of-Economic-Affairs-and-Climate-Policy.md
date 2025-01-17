```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Dutch Ministry of Economic Affairs and Climate Policy"
sort location, dt_announce desc
```
