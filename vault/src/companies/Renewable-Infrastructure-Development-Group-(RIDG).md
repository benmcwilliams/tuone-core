```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Renewable Infrastructure Development Group (RIDG)"
sort location, dt_announce desc
```
