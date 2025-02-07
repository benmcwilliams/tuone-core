```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Iceland-Drilling" or company = "Iceland Drilling")
sort location, dt_announce desc
```
