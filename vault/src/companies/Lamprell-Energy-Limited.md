```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Lamprell-Energy-Limited" or company = "Lamprell Energy Limited")
sort location, dt_announce desc
```
