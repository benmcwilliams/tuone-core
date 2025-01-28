```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "West-Lindsey-District-Council" or company = "West Lindsey District Council")
sort location, dt_announce desc
```
