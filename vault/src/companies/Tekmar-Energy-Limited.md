```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Tekmar-Energy-Limited" or company = "Tekmar Energy Limited")
sort location, dt_announce desc
```
