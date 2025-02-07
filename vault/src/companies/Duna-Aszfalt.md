```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Duna-Aszfalt" or company = "Duna Aszfalt")
sort location, dt_announce desc
```
