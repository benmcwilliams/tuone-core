```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Verlume" or company = "Verlume")
sort location, dt_announce desc
```
