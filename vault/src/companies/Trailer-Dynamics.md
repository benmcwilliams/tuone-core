```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Trailer-Dynamics" or company = "Trailer Dynamics")
sort location, dt_announce desc
```
