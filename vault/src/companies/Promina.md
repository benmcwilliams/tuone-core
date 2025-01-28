```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Promina" or company = "Promina")
sort location, dt_announce desc
```
