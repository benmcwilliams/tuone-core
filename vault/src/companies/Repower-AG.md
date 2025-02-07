```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Repower-AG" or company = "Repower AG")
sort location, dt_announce desc
```
