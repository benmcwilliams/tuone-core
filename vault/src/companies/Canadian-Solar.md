```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Canadian-Solar" or company = "Canadian Solar")
sort location, dt_announce desc
```
