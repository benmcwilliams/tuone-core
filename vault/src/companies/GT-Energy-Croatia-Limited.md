```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "GT-Energy-Croatia-Limited" or company = "GT Energy Croatia Limited")
sort location, dt_announce desc
```
