```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Floating-Solar-BV" or company = "Floating Solar BV")
sort location, dt_announce desc
```
