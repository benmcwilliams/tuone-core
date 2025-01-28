```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Dracula-Technologies" or company = "Dracula Technologies")
sort location, dt_announce desc
```
