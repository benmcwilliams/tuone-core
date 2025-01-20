```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "REG Power Management Ltd"
sort location, dt_announce desc
```
