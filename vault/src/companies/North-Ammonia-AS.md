```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "North-Ammonia-AS" or company = "North Ammonia AS")
sort location, dt_announce desc
```
