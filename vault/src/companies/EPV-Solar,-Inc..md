```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "EPV-Solar,-Inc." or company = "EPV Solar, Inc.")
sort location, dt_announce desc
```
