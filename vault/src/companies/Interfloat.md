```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Interfloat" or company = "Interfloat")
sort location, dt_announce desc
```
