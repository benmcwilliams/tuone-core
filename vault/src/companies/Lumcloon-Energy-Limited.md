```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Lumcloon-Energy-Limited" or company = "Lumcloon Energy Limited")
sort location, dt_announce desc
```
