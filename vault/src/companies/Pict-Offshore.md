```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Pict-Offshore" or company = "Pict Offshore")
sort location, dt_announce desc
```
