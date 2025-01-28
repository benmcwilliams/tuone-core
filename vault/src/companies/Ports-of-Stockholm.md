```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ports-of-Stockholm" or company = "Ports of Stockholm")
sort location, dt_announce desc
```
