```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Manor-Marine" or company = "Manor Marine")
sort location, dt_announce desc
```
