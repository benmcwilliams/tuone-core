```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Norwegian-Crystals" or company = "Norwegian Crystals")
sort location, dt_announce desc
```
