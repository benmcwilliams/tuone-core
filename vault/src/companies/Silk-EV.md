```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Silk-EV" or company = "Silk EV")
sort location, dt_announce desc
```
