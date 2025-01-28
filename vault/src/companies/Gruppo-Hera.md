```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Gruppo-Hera" or company = "Gruppo Hera")
sort location, dt_announce desc
```
