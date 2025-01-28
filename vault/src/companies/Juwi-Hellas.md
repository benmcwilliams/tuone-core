```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "juwi-Hellas" or company = "juwi Hellas")
sort location, dt_announce desc
```
