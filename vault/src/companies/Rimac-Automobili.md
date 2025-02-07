```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Rimac-Automobili" or company = "Rimac Automobili")
sort location, dt_announce desc
```
