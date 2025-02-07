```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "EPZ-Borssele" or company = "EPZ Borssele")
sort location, dt_announce desc
```
