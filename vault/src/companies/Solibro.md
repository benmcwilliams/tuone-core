```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solibro" or company = "Solibro")
sort location, dt_announce desc
```
