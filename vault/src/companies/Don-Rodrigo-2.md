```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Don-Rodrigo-2" or company = "Don Rodrigo 2")
sort location, dt_announce desc
```
