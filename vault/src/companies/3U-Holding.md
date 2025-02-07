```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "3U-Holding" or company = "3U Holding")
sort location, dt_announce desc
```
