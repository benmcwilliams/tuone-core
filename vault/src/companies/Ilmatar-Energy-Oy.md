```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ilmatar-Energy-Oy" or company = "Ilmatar Energy Oy")
sort location, dt_announce desc
```
