```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "BP-Aberdeen-Hydrogen-Energy-Limited" or company = "BP Aberdeen Hydrogen Energy Limited")
sort location, dt_announce desc
```
