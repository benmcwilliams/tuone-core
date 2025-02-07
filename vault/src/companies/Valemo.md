```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Valemo" or company = "Valemo")
sort location, dt_announce desc
```
