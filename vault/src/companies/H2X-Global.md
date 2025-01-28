```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "H2X-Global" or company = "H2X Global")
sort location, dt_announce desc
```
